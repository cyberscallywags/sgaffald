#!/bin/sh
set -e
case "$SERVICE" in
  api)   exec uvicorn app.api.main:app --host 0.0.0.0 --port 8000 ;;
  ui)    exec uvicorn app.ui.main:app --host 0.0.0.0 --port 8080 ;;
  admin)
    APP_DIR=$(python -c "import os, app.admin as a; print(os.path.dirname(a.__file__))")
    exec streamlit run "$APP_DIR/main.py" --server.address 0.0.0.0 --server.port 8501 \
      --server.headless true --browser.gatherUsageStats false ;;
  *) echo "Unknown SERVICE '$SERVICE' (expected api|ui|admin)" >&2; exit 1 ;;
esac
