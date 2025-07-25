#!/bin/sh
export PATH="/var/runtime:/var/task:$PATH"
export PYTHONPATH="/var/task/src:$PYTHONPATH"
exec python -m uvicorn web_app_unified:app --host 0.0.0.0 --port $PORT