#!/bin/sh
set -e

export $(cat .env.local | xargs)
# poetry run python dev-tools/forward_updates.py &
poetry run uvicorn bot.main:app --reload
