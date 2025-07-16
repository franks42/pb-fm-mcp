# jqpy - A jq-like JSON processor in Python

`jqpy` is a Python implementation of a jq-like command-line JSON processor with a powerful path expression language.

## Features

- **jq-like path expressions** for querying JSON data
- **Selector syntax** for filtering with conditions (e.g., `users.*[?(@.active==true)].name`)
- **Flexible output** with pretty-printing, compact mode, and raw output options
- **Easy installation** via pip
- **Pure Python** - no external dependencies

## Installation

```bash
# Install from source
git clone https://github.com/yourusername/hastra-fm-mcp.git
cd haskell-fm-mcp
pip install -e .
```

## Command-Line Usage

```bash
# Basic usage
$ echo '{"name": "John", "age": 30}' | jqpy 'name'
"John"

# Nested access
$ echo '{"user": {"name": "John", "age": 30}}' | jqpy 'user.name'
"John"

# Array access
$ echo '{"items": [1, 2, 3]}' | jqpy 'items[0]'
1

# Wildcard access
$ echo '{"users": [{"name": "John"}, {"name": "Jane"}]}' | jqpy 'users.*.name'
[
  "John",
  "Jane"
]

# Selector syntax
$ echo '{"users": [{"name": "John", "active": true}, {"name": "Jane", "active": false}]}' \
  | jqpy 'users.*[?(@.active==true)].name'
[
  "John"
]

# Raw output (no JSON quotes for strings)
$ echo '{"name": "John"}' | jqpy -r 'name'
John

# From file
$ jqpy 'path.to.value' data.json
```

## Library Usage

```python
from jqpy import get_path

data = {
    "users": [
        {"name": "John", "age": 30, "active": True},
        {"name": "Jane", "age": 25, "active": False}
    ]
}

# Get all active user names
active_users = list(get_path(data, 'users.*[?(@.active==true)].name'))
print(active_users)  # ['John']
```

## Development

To run the tests:

```bash
bash run_jqpy_tests.sh
```

## License

MIT

---

# Python Workers: FastMCP Example

This is an example of a Python Worker that uses the FastMCP package.

[![Deploy to Workers](https://deploy.workers.cloudflare.com/button)](https://deploy.workers.cloudflare.com/?url=https://github.com/danlapid/python-workers-mcp/)

>[!NOTE]
>Due to the [size](https://developers.cloudflare.com/workers/platform/limits/#worker-size) of the Worker, this example can only be deployed if you're using the Workers Paid plan. Free plan users will encounter deployment errors because this Worker exceeds the 3MB size limit.

## Developing and Deploying

To develop your Worker run:

```console
uv run pywrangler dev

Test:
https://playground.ai.cloudflare.com/
connect to "http://localhost:8787/mcp/"
```

To deploy your Worker run:

```console
uv run pywrangler deploy

Test:
https://playground.ai.cloudflare.com/
connect to "https://hastra-fm-mcp.frank-siebenlist.workers.dev/mcp"

```

## Testing

To test run:

```console
uv run pytest tests
```

## Linting and Formatting

This project uses Ruff for linting and formatting:

```console
uv ruff format . --check
uv ruff check .
```

## IDE Integration

To have good autocompletions in your IDE simply select .venv-workers/bin/python as your IDE's interpreter.
