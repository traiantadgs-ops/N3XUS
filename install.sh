#!/data/data/com.termux/files/usr/bin/bash
pkg update -y
pkg install python git curl -y
pip install flask
curl -O https://raw.githubusercontent.com/traiantadgs-ops/N3XUS/main/N3XUS.py
python N3XUS.py
