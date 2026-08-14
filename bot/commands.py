from logging import getLogger
from typing import Awaitable, Callable, Literal

from telegram import (BotCommand, BotCommandScopeChat, Chat,
                      InlineKeyboardButton, InlineKeyboardMarkup, Message,
                      Update)
from telegram.ext import ContextTypes
from telegram.helpers import escape_markdown

from .scaleway import Scaleway

DEFAULT_CONTEXT = ContextTypes.DEFAULT_TYPE
SERVERACTIONS = Literal['poweron', 'poweroff']

logger = getLogger(__name__)

commands = [
    BotCommand('start', 'print list of commands'),
    BotCommand('help', 'print list of commands'),
    BotCommand('set_commands', 'set commands menu'),
    BotCommand('list_servers', 'list scaleway servers'),
    BotCommand('poweron', 'poweron scaleway server'),
    BotCommand('poweroff', 'poweroff scaleway server')
]
command_lines = [f'/{cmd.command} - {cmd.description}' for cmd in commands]


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


def escape(text: str): return escape_markdown(text, version=2)


class Commands:
    def __init__(self, allowed_chats: set[int]):
        self.allowed_chats = allowed_chats

    def check_chat(self, chat: Chat):
        if chat.id not in self.allowed_chats:
            raise PermissionError(f'chat {chat.id} not allowed')

    @only_allowed_chats
    async def start_command(self, message: Message, context: DEFAULT_CONTEXT):
        await message.reply_text('\n'.join(command_lines))

    @only_allowed_chats
    async def set_commands(self, message: Message, context: DEFAULT_CONTEXT):
        scope = BotCommandScopeChat(message.chat.id)
        await context.bot.set_my_commands(commands, scope)
        await message.reply_text('The commands have been set')

    @only_allowed_chats
    async def list_servers(self, message: Message, context: DEFAULT_CONTEXT):
        servers = await Scaleway().list_servers()
        servers_lines = [f'*{escape(s.name)}*: _{escape(s.state)}_'
                         for s in servers]
        await message.reply_markdown_v2('\n'.join(servers_lines))

    @staticmethod
    async def ask_which_server(message: Message, action: SERVERACTIONS):
        servers = await Scaleway().list_servers()
        keyboard = [
            InlineKeyboardButton(s.name, callback_data=f'{action}:{s.id}')
            for s in servers
        ]
        await message.reply_markdown_v2(
            f'Which server do you want to *{action}*?',
            reply_markup=InlineKeyboardMarkup.from_column(keyboard)
        )

    @only_allowed_chats
    async def poweron(self, message: Message, context: DEFAULT_CONTEXT):
        await self.ask_which_server(message, action='poweron')

    @only_allowed_chats
    async def poweroff(self, message: Message, context: DEFAULT_CONTEXT):
        await self.ask_which_server(message, action='poweroff')
