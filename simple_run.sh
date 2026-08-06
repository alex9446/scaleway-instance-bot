set -e

export $(cat .env.local | xargs)
poetry run uvicorn bot.main:app --host 0.0.0.0 --port 8000 --reload
