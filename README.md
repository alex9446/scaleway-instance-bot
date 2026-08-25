# Scaleway Instance Bot

A Telegram bot for listing and powering on or off Scaleway Instances. It is served by FastAPI and processes Telegram updates through a protected webhook.

## Requirements

- Python 3.12+
- Poetry
- A Telegram bot token
- Scaleway API credentials with permission to list and control Instances

## Configuration

Create `.env.local` for local development:

```env
BOT_TOKEN=<telegram-bot-token>
SECRET_TOKEN=<webhook-secret>
ALLOWED_CHATS=<telegram-chat-id>,<another-chat-id>

SCW_ACCESS_KEY=<access-key>
SCW_SECRET_KEY=<secret-key>
```

## Local development

```sh
poetry install
./dev-tools/simple_run.sh
```

The helper starts Uvicorn on `http://localhost:8000` and forwards Telegram updates using long polling. Alternatively, run the application directly:

```sh
poetry run uvicorn bot.main:app
```

For formatting and static checks:

```sh
./dev-tools/check_code.sh
```

## Docker

Build and run the container:

```sh
docker build -t scaleway-instance-bot .
docker run --rm -p 8000:8000 --env-file .env.local scaleway-instance-bot
```

## Set webhook endpoint

The container exposes port `8000` and serves `POST /webhook`. Configure Telegram to send updates to an HTTPS URL pointing to that endpoint, using the same secret configured in `SECRET_TOKEN`:

```sh
curl "https://api.telegram.org/bot${BOT_TOKEN}/setWebhook" \
  --data-urlencode "url=https://<your-domain>/webhook" \
  --data-urlencode "secret_token=${SECRET_TOKEN}"
```

Every deployment to `master` builds and publishes `ghcr.io/<owner>/scaleway-instance-bot:latest` through GitHub Actions.
