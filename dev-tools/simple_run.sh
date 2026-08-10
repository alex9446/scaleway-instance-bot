set -e

export $(cat .env.local | xargs)
poetry run uvicorn bot.main:app --reload
