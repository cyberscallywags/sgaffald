"""Start one service: python -m app.serve [api|ui|admin].

The Docker images run this as their entrypoint (SERVICE comes from the build). Being plain
Python, it runs the same on Windows, macOS and Linux, with no line endings or execute bit to break.
"""

import os
import sys
from pathlib import Path

PORTS = {"api": 8000, "ui": 8080}


def main(argv: list[str] | None = None) -> None:
    args = sys.argv[1:] if argv is None else argv
    service = args[0] if args else os.environ.get("SERVICE", "")
    host = os.environ.get("HOST", "0.0.0.0")  # noqa: S104 - reachable from outside the container
    if service in PORTS:
        import uvicorn

        uvicorn.run(f"app.{service}.main:app", host=host, port=PORTS[service])
    elif service == "admin":
        from streamlit.web import cli

        import app.admin

        script = Path(app.admin.__file__).parent / "main.py"
        sys.argv = [
            "streamlit", "run", str(script),
            "--server.address", host, "--server.port", "8501",
            "--server.headless", "true", "--browser.gatherUsageStats", "false",
        ]  # fmt: skip
        sys.exit(cli.main())
    else:
        sys.exit(f"Unknown SERVICE '{service}' (expected api|ui|admin)")


if __name__ == "__main__":
    main()
