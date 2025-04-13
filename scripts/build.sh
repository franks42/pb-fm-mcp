#!/bin/bash
set -e

# Check if Python 3.12 is installed
if ! command -v python3.12 &> /dev/null; then
    echo "Error: Python 3.12 is required but not installed."
    exit 1
fi

# Create Python virtual environment
if [ ! -d ".venv" ]; then
    echo "Creating Python virtual environment (.venv)..."
    python3.12 -m venv .venv
else
    echo "Using existing Python virtual environment (.venv)..."
fi


# Create pyodide virtual environment if it doesn't exist
if [ ! -d ".venv-pyodide" ]; then
    # Activate the Python virtual environment
    echo "Activating Python virtual environment..."
    source .venv/bin/activate

    # Install pyodide-build in the Python venv
    echo "Installing pyodide-build..."
    pip install pyodide-build
    
    echo "Creating pyodide virtual environment (.venv-pyodide)..."
    pyodide venv .venv-pyodide
    
    # Deactivate the virtual environment
    echo "Deactivating Python virtual environment..."
    deactivate
else
    echo "Using existing pyodide virtual environment (.venv-pyodide)..."
fi

# Download vendored packages
echo "Installing vendored packages from vendor.txt..."
.venv-pyodide/bin/pip install -t src/vendor -r vendor.txt

echo "Build completed successfully!"
