#!/bin/bash
set -e
set -x

git config --global user.email "echel0n@sickrage.ca"
git config --global user.name "echel0n"

pip install --upgrade -r requirements.txt -c constraints.txt

chmod +x tests/*.py
python -m unittest discover tests
