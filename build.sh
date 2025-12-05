#!/usr/bin/env bash
# Render build script

set -o errexit

# Install Python dependencies
pip install --upgrade pip
pip install -r requirements.txt

# Download spaCy model
python -m spacy download en_core_web_sm

# Create necessary directories
mkdir -p chroma_data logs

echo "Build completed successfully!"
