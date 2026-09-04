from asyncio import sleep
from typing import Awaitable, Callable, ParamSpec, TypeVar

from telegram import Message
from telegram.constants import ChatAction
from telegram.error import TimedOut
from telegram.ext import ContextTypes
from telegram.helpers import escape_markdown

from .utils import ExceptionWrapper, logger

DEFAULT_CONTEXT = ContextTypes.DEFAULT_TYPE

P = ParamSpec('P')
T = TypeVar('T')

MAX_ATTEMPTS = 5


async def telegram_retry(f: Callable[P, Awaitable[T]],
                         *args: P.args, **kwargs: P.kwargs) -> T:
    for attempt in range(MAX_ATTEMPTS):
        try:
            return await f(*args, **kwargs)
        except TimedOut as e:
            logger.warning('%s at attempt %s', ExceptionWrapper(e), attempt+1)
            await sleep(1)
            if attempt == MAX_ATTEMPTS - 1:
                raise
    assert False


def escape(text: str): return escape_markdown(text, version=2)


async def silent_typing(message: Message):
    try:
        return await message.reply_chat_action(ChatAction.TYPING)
    except TimedOut:
        return False
