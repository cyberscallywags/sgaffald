"""Run the API and the web UI on this machine with live reload, and no Docker or Neo4j: items
live in memory (STORAGE=memory) and are gone when you stop. The quickest way to try the
template or work on a screen.

    uv run task dev        # API on http://localhost:8000/docs, web UI on http://localhost:8080

Ctrl+C stops both. The mobile app, admin portal and docs need `uv run task up`.
"""

import os
import signal
import subprocess
import sys

SERVICES = {"api": ("app.api.main:app", 8000), "ui": ("app.ui.main:app", 8080)}


def main() -> int:
    env = {**os.environ, "STORAGE": "memory", "API_URL": "http://localhost:8000"}
    procs = [
        subprocess.Popen(  # noqa: S603 - fixed commands
            [sys.executable, "-m", "uvicorn", target, "--port", str(port), "--reload"], env=env
        )
        for target, port in SERVICES.values()
    ]
    print("API http://localhost:8000/docs · web UI http://localhost:8080 · Ctrl+C to stop")
    try:
        return max(proc.wait() for proc in procs)
    except KeyboardInterrupt:
        for proc in procs:
            proc.send_signal(signal.SIGINT)
        return max(proc.wait() for proc in procs)


if __name__ == "__main__":
    sys.exit(main())
