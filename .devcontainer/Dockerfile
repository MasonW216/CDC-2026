# StormRoute dev container: Python 3.11 base plus the system geospatial libraries.
FROM mcr.microsoft.com/devcontainers/python:1-3.11-bookworm

# The base image ships a Yarn apt source whose signing key is missing, which makes
# every `apt-get update` fail, including the ones dev-container features run. The
# project uses npm, so the source is removed before anything touches apt.
RUN grep -rl 'dl.yarnpkg.com' /etc/apt/sources.list.d/ | xargs -r rm -f \
    && apt-get update \
    && apt-get install -y --no-install-recommends \
        gdal-bin libgdal-dev libgeos-dev libproj-dev proj-bin make \
    && rm -rf /var/lib/apt/lists/*
