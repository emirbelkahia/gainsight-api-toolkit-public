import os
import sys
import json
import requests

def main():
    domain = os.environ.get("GAINSIGHT_DOMAIN")
    access_key = os.environ.get("GAINSIGHT_ACCESS_KEY")

    if not domain or not access_key:
        print("Missing env vars. Set GAINSIGHT_DOMAIN and GAINSIGHT_ACCESS_KEY.")
        sys.exit(1)

    url = f"{domain.rstrip('/')}/v1/users/services/list"  # read-only user listing
    headers = {
        "Content-Type": "application/json",
        "Accept": "application/json",
        "accesskey": access_key,  # Gainsight header for API auth
    }

    # Strictly READ parameters: limit small, select a few safe fields
    body = {
        "includeTotal": True,
        "limit": 1,
        "page": 0,
        "orderBy": {"ModifiedDate": "desc"},
        "select": ["Name", "Email", "SFDCUserName", "LicenseType", "ModifiedDate"]
        # no 'where' needed; no writes possible in this call
    }

    try:
        resp = requests.post(url, headers=headers, data=json.dumps(body), timeout=20)
        print(f"HTTP {resp.status_code}")
        # Try to pretty-print JSON if possible
        try:
            print(json.dumps(resp.json(), indent=2))
        except Exception:
            print(resp.text)
        resp.raise_for_status()
        print("\n✅ API key looks valid and endpoint reachable.")
    except requests.RequestException as e:
        print("\n❌ Request failed.")
        print(e)

if __name__ == "__main__":
    main()