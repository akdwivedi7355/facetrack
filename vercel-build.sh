#!/bin/bash
echo "Installing dlib from wheel..."
pip install --no-cache-dir vendor/dlib-19.24.1-cp312-cp312-manylinux_2_17_x86_64.whl

# Install Python dependencies
echo "Installing Python dependencies..."
pip install --no-cache-dir -r requirements.txt

# Install the manually downloaded dlib package
