import redis
from config import CONFIG
from loguru import logger

class ServingCounter:
    """
    Redis-based rate limiter for miner requests.

    Uses atomic Redis operations to track and limit request rates per miner.

    Attributes:
        rate_limit (int): Max requests allowed per epoch
        redis_client (redis.Redis): Redis connection for distributed counting
        key (str): Unique Redis key for this counter
        expire_time (int): TTL for counter keys in Redis
    """

    def __init__(
        self,
        rate_limit: int,
        uid: int,
        redis_client: redis.Redis,
        postfix_key: str = "",
    ):
        self.rate_limit = rate_limit
        self.redis_client = redis_client
        self.key = CONFIG.redis.serving_counter_key_format.format(
            uid=uid,
        ) + str(postfix_key)

    def increment(self) -> bool:
        """
        Increment request counter and check rate limit.

        Uses atomic Redis INCR operation and sets expiry on first increment.

        Reset the counter after EPOCH_LENGTH seconds.

        Returns:
            bool: True if under rate limit, False if exceeded
        """
        count = self.redis_client.incr(self.key)

        if count == 1:
            self.redis_client.expire(self.key, CONFIG.epoch_length)

        if count <= self.rate_limit:
            return True

        logger.info(f"Rate limit exceeded for {self.key}")
        return False

    def get_current_count(self):
        return self.redis_client.get(self.key)

    def reset_counter(self):
        self.redis_client.set(self.key, 0)