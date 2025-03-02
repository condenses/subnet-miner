from pydantic_settings import BaseSettings
from typing import Optional
from pydantic import BaseModel

class SidecarBittensorConfig(BaseModel):
    base_url: str = "http://localhost:9100"

class RedisConfig(BaseModel):
    host: str = "localhost"
    port: int = 6379
    db: int = 0
    username: Optional[str] = None
    password: Optional[str] = None
    serving_counter_key_format: str = "serving_counter:{uid}"


class Settings(BaseSettings):
    redis: RedisConfig = RedisConfig()
    sidecar_bittensor: SidecarBittensorConfig = SidecarBittensorConfig()
    wallet_name: str = "default"
    wallet_hotkey: str = "default"
    wallet_path: str = "~/.bittensor/wallets"
    netuid: int = 47
    axon_port: int = 8091
    subtensor_network: str = "finney"
    min_stake: float = 10000.0
    epoch_length: int = 600


    class Config:
        env_nested_delimiter = "__"
        env_file = ".env"
        extra = "ignore"

CONFIG = Settings()

from rich.console import Console
from rich.panel import Panel

console = Console()
settings_dict = CONFIG.model_dump()

for section, values in settings_dict.items():
    console.print(
        Panel.fit(
            str(values),
            title=f"[bold blue]{section}[/bold blue]",
            border_style="green",
        )
    )
