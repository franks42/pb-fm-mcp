# Python Workers: FastMCP Example

This is an example of a Python Worker that uses the FastMCP package.

[![Deploy to Workers](https://deploy.workers.cloudflare.com/button)](https://deploy.workers.cloudflare.com/?url=https://github.com/danlapid/python-workers-mcp/)

>[!NOTE]
>Due to the [size](https://developers.cloudflare.com/workers/platform/limits/#worker-size) of the Worker, this example can only be deployed if you're using the Workers Paid plan. Free plan users will encounter deployment errors because this Worker exceeds the 3MB size limit.

## Adding Packages

Vendored packages are added to your source files and need to be installed in a special manner. The Python Workers team plans to make this process automatic in the future, but for now, manual steps need to be taken.

### Vendoring Packages

First, install Python3.12 and pip for Python 3.12.

*Currently, other versions of Python will not work - use 3.12!*

Then set up your local pyodide virtual environment:
```console
npm run build
```

### Developing and Deploying

To develop your Worker run:
```console
npm run dev
```

To deploy your Worker run:
```console
npm run deploy
```

### Testing

To test run:
```console
npm run test
```

### Linting and Formatting

This project uses Ruff for linting and formatting:

```console
npm run lint
```

### IDE Integration

To have good autocompletions in your IDE simply select .venv-pyodide/bin/python as your IDE's interpreter.

You should also install your dependencies for type hints.

```console
.venv-pyodide/bin/pip install -r requirements-dev.txt
```
