#!/usr/bin/env python3
"""
Docker health check script for Gumstamp.
This script is used by Docker to determine container health.
"""

import sys
import os
import json
from urllib.request import urlopen
from urllib.error import URLError

def check_health():
    """Check application health and return appropriate exit code"""
    try:
        port = os.environ.get("PORT", "10000")
        base = f"http://localhost:{port}"
        # Check basic health endpoint
        with urlopen(f"{base}/healthz", timeout=5) as resp:
            if resp.status != 200:
                print(f"Health check failed with status {resp.status}", file=sys.stderr)
                return 1
        
        # Check comprehensive health status
        with urlopen(f"{base}/health", timeout=5) as resp:
            if resp.status != 200:
                print(f"Detailed health check failed with status {resp.status}", file=sys.stderr)
                return 1
            body = resp.read().decode("utf-8")
        
        health_data = json.loads(body)
        status = health_data.get("status", "unknown")
        
        if status == "unhealthy":
            print(f"Application reports unhealthy status", file=sys.stderr)
            return 1
        elif status == "degraded":
            print(f"Application reports degraded performance", file=sys.stderr)
            # Return 0 for degraded but still functional
        
        print(f"Health check passed: {status}")
        return 0
        
    except URLError as e:
        print(f"Health check request failed: {e}", file=sys.stderr)
        return 1
    except Exception as e:
        print(f"Health check error: {e}", file=sys.stderr)
        return 1

if __name__ == "__main__":
    sys.exit(check_health())