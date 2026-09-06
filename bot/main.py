from contextlib import asynccontextmanager
from os import getenv
from secrets import compare_digest

from fastapi import FastAPI, Request, Response, status
from telegram import Update
from telegram.ext import (ApplicationBuilder, CallbackQueryHandler,
                          CommandHandler, MessageHandler, filters)

from .commands import Commands
from .scaleway import try_redeploy
from .telegram_utils import DEFAULT_CONTEXT
from .utils import log_exception, logger

SECRET_HEADER = 'X-Telegram-Bot-Api-Secret-Token'
BOT_TOKEN = getenv('BOT_TOKEN')
SECRET_TOKEN = getenv('SECRET_TOKEN')
ALLOWED_CHATS = getenv('ALLOWED_CHATS')

if not (BOT_TOKEN and SECRET_TOKEN and ALLOWED_CHATS):
    required_variables = 'BOT_TOKEN, SECRET_TOKEN, ALLOWED_CHATS'
    raise RuntimeError(f'missing required variables: {required_variables}')

REDEPLOY_HEADER = 'X-Deploy-Secret-Token'
REDEPLOY_TOKEN = getenv('REDEPLOY_TOKEN')

telegram_app = ApplicationBuilder().token(BOT_TOKEN).build()


@asynccontextmanager
async def lifespan(app: FastAPI):
    async with telegram_app:
        yield

app = FastAPI(lifespan=lifespan)


async def telegram_error_handler(update: object | None,
                                 context: DEFAULT_CONTEXT):
    log_exception('exception in handler', context.error)

telegram_app.add_error_handler(telegram_error_handler)

allowed_chats_list = set(map(int, ALLOWED_CHATS.split(',')))
commands = Commands(allowed_chats_list)

telegram_app.add_handlers([
    CommandHandler(['start', 'help'], commands.start_or_help),
    CommandHandler('info', commands.info),
    CommandHandler('redeploy', commands.redeploy),
    CommandHandler('set_commands', commands.set_commands),
    CommandHandler('list_servers', commands.list_servers),
    MessageHandler(filters.COMMAND, commands.maybe_action),
    CallbackQueryHandler(commands.ask_callback)
])


@app.post('/webhook')
async def telegram_webhook(request: Request):
    try:
        host = request.client and request.client.host
        logger.info('new request from %s', host)
        r_secret = request.headers.get(SECRET_HEADER, '')
        if not (SECRET_TOKEN and compare_digest(r_secret, SECRET_TOKEN)):
            logger.warning('wrong telegram secret token from %s', host)
            return Response(status_code=status.HTTP_401_UNAUTHORIZED)

        update = Update.de_json(await request.json(), telegram_app.bot)
        await telegram_app.process_update(update)

        return Response(status_code=status.HTTP_200_OK)
    except Exception as e:
        log_exception('unhandled exception', e)
        return Response(status_code=status.HTTP_200_OK)


@app.post('/redeploy')
async def redeploy(request: Request):
    try:
        host = request.client and request.client.host
        logger.info('redeploy request from %s', host)
        r_secret = request.headers.get(REDEPLOY_HEADER, '')
        if not (REDEPLOY_TOKEN and compare_digest(r_secret, REDEPLOY_TOKEN)):
            logger.warning('wrong redeploy secret token from %s', host)
            return Response(status_code=status.HTTP_401_UNAUTHORIZED)

        success, message = await try_redeploy()
        sc = status.HTTP_200_OK if success else status.HTTP_404_NOT_FOUND
        return Response(message, status_code=sc)
    except Exception as e:
        log_exception('unhandled exception', e)
        return Response(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR)
