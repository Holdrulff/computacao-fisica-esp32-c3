#!/bin/bash
#
# ESP32 Deploy Script - Wrapper para deploy.py
# Uso: ./deploy.sh [PORT]
#

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
VENV_DIR="$SCRIPT_DIR/venv"

echo "==================================="
echo "ESP32 Deployment Script"
echo "==================================="
echo ""

# Check if venv exists
if [ ! -d "$VENV_DIR" ]; then
    echo "⚠️  Virtual environment not found at: $VENV_DIR"
    echo "Creating virtual environment..."
    python -m venv "$VENV_DIR"
    echo "✓ Virtual environment created"
    echo ""
fi

# Activate venv
echo "Activating virtual environment..."
source "$VENV_DIR/Scripts/activate"

# Check if mpremote is installed
if ! command -v mpremote &> /dev/null; then
    echo "⚠️  mpremote not found. Installing..."
    pip install mpremote
    echo "✓ mpremote installed"
    echo ""
fi

# Run deployment script
echo "Starting deployment..."
echo ""

if [ -z "$1" ]; then
    python "$SCRIPT_DIR/deploy.py"
else
    python "$SCRIPT_DIR/deploy.py" "$1"
fi

# Keep venv activated for manual commands if needed
echo ""
echo "Virtual environment is still active."
echo "You can run manual mpremote commands or type 'deactivate' to exit."
