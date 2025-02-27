import bittensor as bt
from pydantic import Field

class TextCompressProtocol(bt.Synapse):
    id: str = ""
    context: str = ""
    compressed_context: str = ""
    user_message: str = ""
    compress_rate: float = 0.0

