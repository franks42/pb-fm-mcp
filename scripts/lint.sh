source .venv/bin/activate
pip install ruff
ruff format .  # Format code
ruff check .  # Run linting