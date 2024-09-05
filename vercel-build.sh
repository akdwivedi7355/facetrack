#!/bin/bash
# Set up Python 3.11
/bin/bash setup-python.sh

# Use Python 3.11 and pip3.11 for installations
python3.11 -m venv venv
source venv/bin/activate

echo "Installing dlib from wheel..."
pip install vendor/dlib-19.24.1-cp311-cp311-manylinux_2_17_x86_64.whl

echo "Installing Python dependencies..."
pip install -r requirements.txt
