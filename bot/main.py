from contextlib import asynccontextmanager
from os import getenv
from sys import stderr

from fastapi import FastAPI, Request, Response, status
from telegram import Update
from telegram.ext import ApplicationBuilder, CommandHandler

from .commands import Commands

SECRET_HEADER = 'X-Telegram-Bot-Api-Secret-Token'
BOT_TOKEN = getenv('BOT_TOKEN')
SECRET_TOKEN = getenv('SECRET_TOKEN')
ALLOWED_CHATS = getenv('ALLOWED_CHATS')

if not (BOT_TOKEN and SECRET_TOKEN and ALLOWED_CHATS):
    required_variables = 'BOT_TOKEN, SECRET_TOKEN, ALLOWED_CHATS'
    raise RuntimeError(f'missing required variables: {required_variables}')

telegram_app = ApplicationBuilder().token(BOT_TOKEN).build()


@asynccontextmanager
async def lifespan(app: FastAPI):
    await telegram_app.initialize()
    await telegram_app.start()
    yield
    await telegram_app.stop()
    await telegram_app.shutdown()

app = FastAPI(lifespan=lifespan)

allowed_chats_list = list(map(int, ALLOWED_CHATS.split(',')))
commands = Commands(allowed_chats_list)

telegram_app.add_handler(
    CommandHandler(['start', 'help'], commands.start_command)
)


@app.post("/webhook")
async def telegram_webhook(request: Request):
    try:
        r_secret = request.headers.get(SECRET_HEADER)
        if r_secret != SECRET_TOKEN:
            raise PermissionError(f'wrong telegram secret token: {r_secret}')

        update = Update.de_json(await request.json(), telegram_app.bot)
        await telegram_app.process_update(update)

        return Response(status_code=status.HTTP_200_OK)
    except Exception as e:
        print(e, file=stderr)
        return Response(status_code=status.HTTP_200_OK)
