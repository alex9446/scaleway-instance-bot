from typing import TYPE_CHECKING, Awaitable, Callable

from telegram import CallbackQuery, Message, Update

from .telegram_utils import DEFAULT_CONTEXT, silent_typing
from .utils import logger

if TYPE_CHECKING:
    from .commands import Commands


def only_allowed_chats_message(
    f: Callable[["Commands", Message, DEFAULT_CONTEXT], Awaitable[None]]
):
    async def w(self: "Commands", update: Update, context: DEFAULT_CONTEXT):
        if message := update.message:
            allowed, chat_id = self.is_chat_allowed(update)
            if allowed:
                await silent_typing(message)
                await f(self, message, context)
            else:
                logger.warning('chat %s not allowed', chat_id)
                await message.reply_text('this chat is not allowed')
        else:
            logger.warning('message is None')
    return w


def only_allowed_chats_callback(
    f: Callable[["Commands", CallbackQuery], Awaitable[None]]
):
    async def w(self: "Commands", update: Update, context: DEFAULT_CONTEXT):
        if callback_query := update.callback_query:
            allowed, chat_id = self.is_chat_allowed(update)
            if allowed:
                await f(self, callback_query)
            else:
                logger.warning('chat %s not allowed', chat_id)
                if message := update.effective_message:
                    await message.reply_text('this chat is not allowed')
        else:
            logger.warning('callback_query is None')
    return w
