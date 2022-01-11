#! /bin/bash

set -e

source .venv/bin/activate

mypy app
python -m pytest --instafail --exitfirst
