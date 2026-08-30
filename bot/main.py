from contextlib import asynccontextmanager
from logging import getLogger
from os import getenv

from fastapi import FastAPI, Request, Response, status
from telegram import Update
from telegram.ext import (ApplicationBuilder, CallbackQueryHandler,
                          CommandHandler, MessageHandler, filters)

from .commands import DEFAULT_CONTEXT, Commands
from .utils import can_reach_telegram

logger = getLogger('uvicorn.error')

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
    async with telegram_app:
        yield

app = FastAPI(lifespan=lifespan)


async def telegram_error_handler(update: object | None,
                                 context: DEFAULT_CONTEXT):
    logger.critical('exception in handler: %s', context.error)

telegram_app.add_error_handler(telegram_error_handler)

allowed_chats_list = set(map(int, ALLOWED_CHATS.split(',')))
commands = Commands(allowed_chats_list)

telegram_app.add_handlers([
    CommandHandler(['start', 'help'], commands.start_or_help),
    CommandHandler('info', commands.info),
    CommandHandler('set_commands', commands.set_commands),
    CommandHandler('list_servers', commands.list_servers),
    MessageHandler(filters.COMMAND, commands.maybe_action),
    CallbackQueryHandler(commands.ask_callback)
])


@app.post("/webhook")
async def telegram_webhook(request: Request):
    try:
        host = request.client and request.client.host
        logger.info('new request from %s', host)
        r_secret = request.headers.get(SECRET_HEADER)
        if r_secret != SECRET_TOKEN:
            logger.warning('wrong telegram secret token from %s', host)
            return Response(status_code=status.HTTP_403_FORBIDDEN)

        if not can_reach_telegram():
            logger.critical('telegram is unreachable')
        update = Update.de_json(await request.json(), telegram_app.bot)
        await telegram_app.process_update(update)

        return Response(status_code=status.HTTP_200_OK)
    except Exception as e:
        logger.critical('unhandled exception: %s', e)
        return Response(status_code=status.HTTP_200_OK)
