#!/bin/bash

set -e

echo "Producing coverage docs...."
coverage run --source=${PWD}/app -m pytest --instafail --exitfirst
mkdir -p coverage_html
coverage html -d coverage_html