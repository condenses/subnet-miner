# Subnet-miner

## Installation
To install the necessary components, run the following commands:
```
git clone https://github.com/condenses/subnet-miner.git
cd subnet-miner
pip install uv
uv venv
. .venv/bin/activate
uv sync --prerelease=allow
. install_redis.sh
```

## Quick Start
### Sidecar Bittensor
Role: Dedicated process for auto-sync metagraph and chain functions
```
update-env WALLET_NAME default
update-env WALLET_HOTKEY default
update-env WALLET_PATH ~/.bittensor/wallets
pm2 start python --name "sidecar-bittensor" -- -m uvicorn sidecar_bittensor.server:app --host 127.0.0.1 --port 9000
```
### Run miner
```
update-env SIDECAR_BITTENSOR__BASE_URL http://localhost:9000
update-env AXON_PORT port
pm2 start main.py --interpreter python3 --name "sn47-miner"
```
