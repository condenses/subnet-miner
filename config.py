from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    wallet_name: str = "default"
    wallet_hotkey: str = "default"
    wallet_path: str = "~/.bittensor/wallets"
    netuid: int = 245
    axon_port: int = 8091
    subtensor_network: str = "test"
    min_stake: float = 0.0


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