import http.client
import urllib.parse
from typing import Optional


def verify_license(license_key: str, product_permalink: str) -> Optional[dict]:
    """Verify a Gumroad license key against a product permalink.

    Returns a dict on success or None on failure.
    """
    # Using Gumroad simple verification endpoint
    # POST https://api.gumroad.com/v2/licenses/verify
    params = urllib.parse.urlencode({
        "product_permalink": product_permalink,
        "license_key": license_key,
    })
    headers = {"Content-Type": "application/x-www-form-urlencoded"}
    conn = http.client.HTTPSConnection("api.gumroad.com", timeout=10)
    try:
        conn.request("POST", "/v2/licenses/verify", params, headers)
        resp = conn.getresponse()
        if resp.status != 200:
            return None
        import json

        data = json.loads(resp.read().decode("utf-8"))
        if data.get("success"):
            return data
        return None
    except Exception:
        return None
    finally:
        conn.close()
