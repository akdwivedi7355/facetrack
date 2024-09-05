#!/bin/bash
echo "Installing Python 3.11..."
# Update the package list
sudo apt-get update
# Install dependencies
sudo apt-get install -y software-properties-common
# Add the deadsnakes PPA which includes Python 3.11
sudo add-apt-repository ppa:deadsnakes/ppa
sudo apt-get update
# Install Python 3.11
sudo apt-get install -y python3.11 python3.11-venv python3.11-dev
