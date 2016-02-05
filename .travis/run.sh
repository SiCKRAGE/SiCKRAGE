#!/bin/bash
set -e
set -x

git config --global user.email "sickrage.tv@gmail.com"
git config --global user.name "echel0n"

pip install --upgrade -r requirements/requirements.txt -c requirements/constraints.txt
pip install --upgrade -r requirements/ssl.txt -c requirements/constraints.txt
pip install --upgrade -r requirements/optional.txt -c requirements/constraints.txt
pip install --upgrade configobj

chmod +x tests/*.py
python -m unittest discover tests