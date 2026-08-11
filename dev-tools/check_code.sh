#!/bin/sh
set -e

poetry run flake8 "$@"
poetry run pyright "$@"
poetry run isort "$@"
