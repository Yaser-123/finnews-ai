#!/usr/bin/env bash
# Render build script

set -o errexit

# Install system dependencies needed for spaCy
apt-get update && apt-get install -y gcc g++ build-essential

# Install Python dependencies
pip install --upgrade pip
pip install wheel setuptools
pip install -r requirements-render.txt

# Download spaCy model
python -m spacy download en_core_web_sm

# Create necessary directories
mkdir -p chroma_data logs

echo "Build completed successfully!"
