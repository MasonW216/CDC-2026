#!/usr/bin/env bash
# Installs the system geospatial libraries the Python stack needs.
#
# The base image ships a Yarn apt source whose signing key is missing, which
# makes `apt-get update` fail and aborts the whole Codespace build. The project
# uses npm, not Yarn, so the source is removed first.
set -euo pipefail

grep -rl 'dl.yarnpkg.com' /etc/apt/sources.list.d/ 2>/dev/null | xargs -r sudo rm -f

sudo apt-get update
sudo apt-get install -y --no-install-recommends \
  gdal-bin libgdal-dev libgeos-dev libproj-dev proj-bin make
sudo rm -rf /var/lib/apt/lists/*
