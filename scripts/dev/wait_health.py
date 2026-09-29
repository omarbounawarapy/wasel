"""Wait until the API answers /api/health (used by `make up` before starting the dashboard). Exit 1 after 180 s."""
import sys
import time
import urllib.request

base = (sys.argv[1] if len(sys.argv) > 1 else "http://localhost:8000").rstrip("/")
for _ in range(360):
    try:
        with urllib.request.urlopen(base + "/api/health", timeout=2) as r:
            if r.status == 200:
                sys.exit(0)
    except OSError:
        pass
    time.sleep(0.5)
print(f"API at {base} did not answer /api/health within 180 s", file=sys.stderr)
sys.exit(1)
