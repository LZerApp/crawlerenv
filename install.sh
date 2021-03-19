#!/bin/bash

# ------------------------------
# System Packages
# ------------------------------
sudo apt update && sudo apt upgrade
wget https://dl.google.com/linux/direct/google-chrome-stable_current_amd64.deb
sudo apt install python3-pip unzip
sudo apt install -y -f ./google-chrome-stable_current_amd64.deb
rm ./google-chrome-stable_current_amd64.deb

# ------------------------------
# Download Driver
# ------------------------------
wget https://chromedriver.storage.googleapis.com/89.0.4389.23/chromedriver_linux64.zip
unzip chromedriver_linux64.zip
chmod +x chromedriver
rm ./chromedriver_linux64.zip

# ------------------------------
# Python Package
# ------------------------------
python3 -m pip install virtualenv
python3 -m virtualenv env
source env/bin/activate
pip install -r requirements.txt
