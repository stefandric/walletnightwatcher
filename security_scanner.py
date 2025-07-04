# import requests
# from dotenv import load_dotenv
# import os

# SECURITY_KEY = os.getenv("SECURITY_KEY")


# class SecurityScanner:
#     BASE_URL = "https://api.chainabuse.com/v0/reports"

#     def __init__(self):
#         self.api_key = SECURITY_KEY

#     def check_address(self, address: str, chain: str = "ETH") -> dict:
#         """
#         Checks the provided wallet address for scam reports on Chainabuse.
#         Returns a dict with:
#         - success: True/False
#         - data: dict with 'count' and 'reports' (if success)
#         - error: error message (if failure)
#         """
#         try:
#             response = requests.get(
#                 self.BASE_URL,
#                 params={"chain": chain.upper(), "address": address},
#                 auth=(self.api_key, self.api_key),
#                 headers={"accept": "application/json"},
#                 timeout=10  # Optional: prevent hanging requests
#             )

#             if response.status_code == 200:
#                 data = response.json()
#                 # Normalize: if raw list, wrap it
#                 if isinstance(data, list):
#                     return {
#                         "success": True,
#                         "data": {
#                             "count": len(data),
#                             "reports": data
#                         }
#                     }
#                 else:
#                     return {"success": True, "data": data}

#             return {
#                 "success": False,
#                 "error": f"Status {response.status_code}: {response.text}"
#             }

#         except requests.exceptions.Timeout:
#             return {"success": False, "error": "Request timed out."}

#         except requests.exceptions.RequestException as e:
#             return {"success": False, "error": f"Request failed: {str(e)}"}





# import requests

# class SecurityScanner:
#     BASE_URL = "https://api.gopluslabs.io/api/v1/address_security"

#     def __init__(self):
#         pass  # No API key required for GoPlus

#     def check_address(self, address: str) -> dict:
#         """
#         Checks the given address using GoPlus Security API.
#         Returns a dict with:
#         - success: True/False
#         - data: dict of risk indicators (if success)
#         - error: error message (if failure)
#         """
#         try:
#             url = f"{self.BASE_URL}/{address}"
#             response = requests.get(url, headers={"accept": "application/json"}, timeout=10)

#             if response.status_code != 200:
#                 return {
#                     "success": False,
#                     "error": f"Status {response.status_code}: {response.text}"
#                 }

#             result = response.json()
#             if result.get("code") != 1 or "result" not in result:
#                 return {"success": False, "error": "Invalid response from GoPlus"}

#             return {"success": True, "data": result["result"]}

#         except requests.exceptions.Timeout:
#             return {"success": False, "error": "Request timed out."}
#         except requests.exceptions.RequestException as e:
#             return {"success": False, "error": f"Request failed: {str(e)}"}


import requests

class SecurityScanner:
    BASE_URL = "https://api.gopluslabs.io/api/v1/address_security"

    def __init__(self, chain_id: str = "1"):  # default to Ethereum mainnet
        self.chain_id = chain_id

    def check_address(self, address: str) -> dict:
        """
        Public (unauthenticated) GoPlus API to check address risk on a specific chain.

        Returns:
        {
            "success": True/False,
            "data": {
                "is_malicious": True/False,
                "flags": [List of flagged risk keys]
            }
        }
        """
        url = f"{self.BASE_URL}/{address}"
        params = {"chain_id": self.chain_id}

        try:
            response = requests.get(url, params=params, timeout=10)
            if response.status_code != 200:
                return {"success": False, "error": f"HTTP {response.status_code}: {response.text}"}

            result = response.json()
            if result.get("code") != 1 or "result" not in result:
                return {"success": False, "error": "Invalid response from GoPlus"}

            flags = result["result"]
            triggered = [k for k, v in flags.items() if v == "1"]

            return {
                "success": True,
                "data": {
                    "is_sanctioned": bool(triggered),
                    "flags": triggered
                }
            }

        except requests.exceptions.RequestException as e:
            return {"success": False, "error": str(e)}