# security_scanner.py

import requests
from dotenv import load_dotenv
import os

SECURITY_KEY = os.getenv("SECURITY_KEY")

class SecurityScanner:
    BASE_URL = "https://api.chainabuse.com/v0/reports"

    def __init__(self):
        self.api_key = SECURITY_KEY

    def check_address(self, address: str, chain: str = "ETH") -> dict:
        try:
            response = requests.get(
                self.BASE_URL,
                params={"chain": chain.upper(), "address": address},
                auth=(self.api_key, self.api_key),
                headers={"accept": "application/json"}
            )

            if response.status_code == 200:
                reports = response.json()
                return {"success": True, "data": reports}
            else:
                return {"success": False, "error": f"Status {response.status_code}: {response.text}"}
        except Exception as e:
            return {"success": False, "error": str(e)}