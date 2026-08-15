#!/bin/sh
set -e

poetry run isort "$@"
poetry run flake8 "$@"
poetry run pyright "$@"
