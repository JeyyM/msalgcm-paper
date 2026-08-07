"""Block until the dev API responds on /api/health."""

from __future__ import annotations

import os
import sys
import time
import urllib.error
import urllib.request

PORT = int(os.environ.get("DEV_API_PORT", "8002"))
HEALTH_URL = f"http://127.0.0.1:{PORT}/api/health"
TIMEOUT_SECONDS = 60


def main() -> int:
    deadline = time.time() + TIMEOUT_SECONDS
    while time.time() < deadline:
        try:
            with urllib.request.urlopen(HEALTH_URL, timeout=1) as response:
                if response.status == 200:
                    return 0
        except (urllib.error.URLError, TimeoutError, OSError):
            time.sleep(0.25)
    print(f"API did not become ready at {HEALTH_URL} within {TIMEOUT_SECONDS}s", file=sys.stderr)
    return 1


if __name__ == "__main__":
    raise SystemExit(main())
