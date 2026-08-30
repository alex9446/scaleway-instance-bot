#!/bin/sh
set -e

export $(cat .env.local | xargs)

poetry run python dev-tools/forward_updates.py &

BG_PID=$!
trap "kill $BG_PID" EXIT INT TERM

echo "Build Date: $(date -Is)" > ./build-info.txt
echo "Git Commit: $(git rev-parse HEAD)" >> ./build-info.txt

poetry run uvicorn bot.main:app --log-level debug --reload
