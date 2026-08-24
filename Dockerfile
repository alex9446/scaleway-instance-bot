FROM python:3.14-alpine AS base

RUN adduser -D lp-user
USER lp-user
WORKDIR /home/lp-user/app


FROM base AS builder

RUN pip install --no-cache-dir --user poetry

COPY pyproject.toml poetry.lock ./

ENV PATH="/home/lp-user/.local/bin:$PATH"

ENV POETRY_VIRTUALENVS_IN_PROJECT=true
RUN poetry install --only main --no-interaction --no-ansi --no-root


FROM base AS runtime

COPY --from=builder /home/lp-user/app/.venv ./.venv

COPY bot ./bot

ENV PATH="/home/lp-user/app/.venv/bin:$PATH"

EXPOSE 8000

CMD ["uvicorn", "bot.main:app", "--host", "0.0.0.0", "--port", "8000"]
