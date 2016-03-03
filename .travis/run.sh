#!/bin/bash
set -e
set -x

git config --global user.email "sickrage.tv@gmail.com"
git config --global user.name "echel0n"

pip install --upgrade -r sickrage/requirements.txt
pip install --upgrade configobj

chmod +x tests/*.py
python -m unittest discover tests