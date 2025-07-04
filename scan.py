
# wallet_scanner.py

import requests
from dotenv import load_dotenv
import os

MORALIS_API_KEY = os.getenv("MORALIS_API_KEY")

class WalletScanner:
    def __init__(self):
        self.api_key = MORALIS_API_KEY

    def fetch_evm_portfolio(self, address: str, chain: str) -> dict | None:
        url = f"https://deep-index.moralis.io/api/v2.2/wallets/{address}/tokens?chain={chain}"
        headers = {"x-api-key": self.api_key}
        res = requests.get(url, headers=headers)
        if res.status_code != 200:
            return None
        data = res.json().get("result", [])
        
        total_usd = sum(t.get("usd_value", 0) for t in data)
        native_entry = next((t for t in data if t.get("native_token")), None)
        
        return {
            "native": {
                "symbol": native_entry.get("symbol") if native_entry else chain.upper(),
                "balance": float(native_entry.get("balance", 0)) / 10**int(native_entry.get("decimals",18)),
                "usdValue": native_entry.get("usd_value", 0)
            },
            "tokens": [
                {
                    "symbol": t["symbol"],
                    "usdValue": t.get("usd_value", 0)
                }
                for t in data if not t.get("native_token")
            ],
            "total_usd": total_usd
        }