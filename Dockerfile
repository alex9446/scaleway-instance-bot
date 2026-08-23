FROM python:3-alpine

RUN apk add --no-cache poetry

RUN adduser -D lp-user

WORKDIR /home/lp-user

# prefer not to run as root
USER lp-user

COPY pyproject.toml poetry.lock ./

RUN poetry install --only main

COPY bot ./bot

EXPOSE 8000

CMD ["poetry", "run", "uvicorn", "bot.main:app", "--host", "0.0.0.0", "--port", "8000"]
