#!/usr/bin/env bash
# Render build script

set -o errexit

echo "Python version check:"
python --version

# Install system dependencies needed for spaCy
apt-get update && apt-get install -y gcc g++ build-essential

# Install Python dependencies
pip install --upgrade pip
pip install wheel setuptools
pip install -r requirements-render.txt

# Download spaCy model
python -m spacy download en_core_web_sm

# Pre-build matplotlib font cache to avoid slow first startup
echo "Pre-building matplotlib font cache..."
python -c "import matplotlib.pyplot as plt; import matplotlib.font_manager; print('Font cache built')" || echo "Font cache build failed (non-critical)"

# Create necessary directories
mkdir -p chroma_data logs

echo "Build completed successfully!"
