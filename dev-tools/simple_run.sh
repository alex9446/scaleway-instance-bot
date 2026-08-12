#!/bin/sh
set -e

export $(cat .env.local | xargs)

poetry run python dev-tools/forward_updates.py &

BG_PID=$!
trap "kill $BG_PID" EXIT INT TERM

poetry run uvicorn bot.main:app --reload
