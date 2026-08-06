set -e

poetry run flake8 bot
poetry run pyright bot
poetry run isort bot
