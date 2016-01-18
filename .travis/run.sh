#!/bin/bash
set -e
set -x

chmod +x tests/*.py
python -m unittest discover tests