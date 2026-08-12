from logging import getLogger
from typing import Awaitable, Callable

from telegram import BotCommand, BotCommandScopeChat, Chat, Message, Update
from telegram.ext import ContextTypes

DEFAULT_CONTEXT = ContextTypes.DEFAULT_TYPE

logger = getLogger(__name__)

commands = [
    BotCommand('start', 'print list of commands'),
    BotCommand('help', 'print list of commands'),
    BotCommand('set_commands', 'set commands menu')
]
commands_list = [f'/{cmd.command} - {cmd.description}' for cmd in commands]


def only_allowed_chats(f: Callable[["Commands", Message, DEFAULT_CONTEXT],
                                   Awaitable[None]]):
    async def w(self: "Commands", update: Update, context: DEFAULT_CONTEXT):
        if message := update.message:
            chat_id = message.chat.id
            if chat_id in self.allowed_chats:
                await f(self, message, context)
            else:
                logger.warning('chat %s not allowed', chat_id)
                await message.reply_text('this chat is not allowed')
        else:
            logger.warning('message is None')
    return w


class Commands:
    def __init__(self, allowed_chats: set[int]):
        self.allowed_chats = allowed_chats

    def check_chat(self, chat: Chat):
        if chat.id not in self.allowed_chats:
            raise PermissionError(f'chat {chat.id} not allowed')

    @only_allowed_chats
    async def start_command(self, message: Message, context: DEFAULT_CONTEXT):
        await message.reply_text('\n'.join(commands_list))

    @only_allowed_chats
    async def set_commands(self, message: Message, context: DEFAULT_CONTEXT):
        scope = BotCommandScopeChat(message.chat.id)
        await context.bot.set_my_commands(commands, scope)
        await message.reply_text('The commands have been set')
