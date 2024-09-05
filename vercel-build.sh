#!/bin/bash
# Check if Python is installed
if ! command -v python3 &> /dev/null
then
    echo "Python is not installed. Please install Python."
    exit
fi

# Check if pip is installed
if ! command -v pip &> /dev/null
then
    echo "pip is not installed. Installing pip..."
    python3 -m ensurepip --upgrade
fi

echo "Installing dlib from wheel..."
pip install vendor/dlib-19.24.1-cp312-cp312-manylinux_2_17_x86_64.whl

echo "Installing Python dependencies..."
pip install -r requirements.txt
