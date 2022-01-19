#!/bin/bash

cd docs/
pandoc overview.md config.md deployment.md plugins.md API.md glossary.md -V geometry:margin=1in -f gfm -o ../Readme.pdf
pandoc user_guide.md -V geometry:margin=1in -f gfm -o ../UserGuide.pdf