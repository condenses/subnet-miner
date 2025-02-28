import bittensor as bt
from loguru import logger
from config import CONFIG
from protocol import TextCompressProtocol
from typing import Tuple
import traceback
from llmlingua import PromptCompressor
import time
import asyncio
from sidecar_bittensor.client import AsyncRestfulBittensor
from typing import Dict
from redis_manager import ServingCounter

class MinerCore:
    def __init__(self):
        logger.info("Initializing MinerCore")
        self.wallet = bt.Wallet(
            path=CONFIG.wallet_path,
            name=CONFIG.wallet_name,
            hotkey=CONFIG.wallet_hotkey,
        )
        logger.info(f"Wallet initialized: {self.wallet}")
        self.dendrite = bt.Dendrite(wallet=self.wallet)
        self.compressor = PromptCompressor(
                model_name="microsoft/llmlingua-2-xlm-roberta-large-meetingbank",
                use_llmlingua2=True,
            )
        self.restful_bittensor = AsyncRestfulBittensor(
            CONFIG.sidecar_bittensor.base_url
        )
        self.blacklist_fns = [self.blacklist_fn]
        self.forward_fns = [self.forward_text_compress]
        self.my_subnet_uid,_ = self.getminfo(self.wallet.hotkey.ss58_address)
        if self.mysubnet_uid==-1:
            logger.error(
                f"\nYour miner: {self.wallet} is not registered to chain connection: {self.subtensor} \nRun 'btcli register' and try again."
            )
            exit()
        else:
            logger.info(f"Running miner on uid: {self.my_subnet_uid}")

    def _initialize_rate_limits(self):
        r"""
        Initializes the rate limits for the miners.
        """
        self.rate_limits = {
            uid: ServingCounter(
                rate_limit=rate_limit,
                uid=uid,
                redis_client=self.redis,
                postfix_key=CONFIG.axon_port,
            )
            for uid, rate_limit in self.build_rate_limit(CONFIG.min_stake).items()
        }
        for k, v in self.rate_limits.items():
            v.reset_counter()
            bt.logging.info(
                f"Reset rate limit for {k}: {v.get_current_count()}/{v.rate_limit}"
            )

    def build_rate_limit(self, minstake: int) -> Dict[int, int]:
        response = self.restful_bittensor.get_rate_limit(minstake)
        return response

    def get_miner_info(self, ss58_address: str) -> Tuple[int, float]:
        response = self.restful_bittensor.get_miner_info(ss58_address)
        return response

    def setup_axon(self):
        self.axon = bt.axon(
            wallet=self.wallet,
            port=CONFIG.axon_port,
            external_port=CONFIG.axon_port,
        )
        logger.info("Attaching forward function to axon.")
        for blacklist_fn, forward_fn in zip(self.blacklist_fns, self.forward_fns):
            logger.info(
                f"Attaching blacklist_fn: {blacklist_fn} and forward_fn: {forward_fn}"
            )
            self.axon.attach(
                forward_fn=forward_fn,
                blacklist_fn=blacklist_fn,
            )
        logger.info(
            f"Serving axon on network: {CONFIG.subtensor_network} with netuid: {CONFIG.netuid}"
        )
        self.axon.serve(netuid=CONFIG.netuid, subtensor=self.subtensor)
        logger.info(f"Axon: {self.axon}")
        logger.info(f"Starting axon server on port: {CONFIG.axon_port}")
        self.axon.start()

    def run(self):
        self.setup_axon()
        logger.info("Starting main loop")
        step = 0
        while True:
            try:
                # Periodically update our knowledge of the network graph.
                if step % 60 == 0:
                    self.metagraph.sync()
                    self._initialize_rate_limits()
                    _,incentive = self.get_miner_info(self.wallet.hotkey.ss58_address)
                    log = (
                        f"Incentive: {incentive} | "
                    )
                    logger.info(log)
                step += 1
                time.sleep(10)

            except KeyboardInterrupt:
                self.axon.stop()
                logger.success("Miner killed by keyboard interrupt.")
                break
            except Exception as e:
                logger.error(f"Miner exception: {e}")
                logger.error(traceback.format_exc())
                continue

    def blacklist_fn(
        self, synapse: TextCompressProtocol
    ) -> Tuple[bool, str]:
        r"""
        Blacklist function for the Text-Compress task.
        Args:
            synapse (TextCompressProtocol): The synapse containing the text to compress.
        Returns:
            bool: Whether to blacklist the synapse.
            reason (str): The reason for blacklisting the synapse.
        """
        hotkey = synapse.dendrite.hotkey
        uid,_= self.get_miner_info(hotkey)
        allowed = self.rate_limits[uid].increment()
        logger.info(
            f"Rate limit: {uid} {self.rate_limits[uid].get_current_count()}/{self.rate_limits[uid].rate_limit}"
        )
        if not allowed:
            return True, "Rate limit exceeded."
        return False, ""
    
    async def forward_text_compress(
        self, synapse: TextCompressProtocol
    ) -> TextCompressProtocol:
        r"""
        Forward function for the Text-Compress task.
        Args:
            synapse (TextCompressProtocol): The synapse containing the text to compress.
        Returns:
            TextCompressProtocol: The compressed text.
        """
        start_time = time.perf_counter()
        logger.info(
            f"Forwarding text compress: {synapse.context[:100]}...{synapse.context[-100:]}"
        )
        logger.info(f"Context length: {len(synapse.context)}")
        loop = asyncio.get_event_loop()
        compressed_output = await loop.run_in_executor(
            None,  # None -> dùng default thread pool
            self.compressor.compress_prompt,
            synapse.context,
            0.7,
            ["\n", "?"],
        )
        
        synapse.compressed_context = compressed_output["compressed_prompt"]
        end_time = time.perf_counter()  
        elapsed_time = end_time - start_time
        logger.info(f"Text compression completed in {elapsed_time:.4f} seconds")
        return synapse

    
if __name__=="__main__":
    miner = MinerCore()
    miner.run()

        