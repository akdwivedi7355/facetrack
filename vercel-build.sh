#!/bin/bash
echo "Installing dlib from wheel..."
pip install vendor/dlib-19.24.1-cp312-cp312-manylinux_2_17_x86_64.whl

# Install Python dependencies
echo "Installing Python dependencies..."
pip install -r requirements.txt

# Install the manually downloaded dlib package
