from logging import getLogger
from typing import Awaitable, Callable

from telegram import (BotCommand, BotCommandScopeChat, CallbackQuery,
                      InlineKeyboardButton, InlineKeyboardMarkup, Message,
                      Update)
from telegram.ext import ContextTypes
from telegram.helpers import escape_markdown

from .scaleway import SERVERACTIONS, Scaleway

DEFAULT_CONTEXT = ContextTypes.DEFAULT_TYPE
CHAT_ID = int

logger = getLogger('uvicorn.error')

commands = [
    BotCommand('start', 'print list of commands'),
    BotCommand('help', 'print list of commands'),
    BotCommand('set_commands', 'set commands menu'),
    BotCommand('list_servers', 'list scaleway servers'),
    BotCommand('poweron', 'poweron scaleway server'),
    BotCommand('poweroff', 'poweroff scaleway server')
]
command_lines = [f'/{cmd.command} - {cmd.description}' for cmd in commands]


def only_allowed_chats_message(
    f: Callable[["Commands", Message, DEFAULT_CONTEXT], Awaitable[None]]
):
    async def w(self: "Commands", update: Update, context: DEFAULT_CONTEXT):
        if message := update.message:
            allowed, chat_id = self.is_chat_allowed(update)
            if allowed:
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


def escape(text: str): return escape_markdown(text, version=2)


class Commands:
    def __init__(self, allowed_chats: set[int]):
        self.allowed_chats = allowed_chats

    def is_chat_allowed(self, update: Update) -> tuple[bool, CHAT_ID]:
        if chat := update.effective_chat:
            chat_id = chat.id
            if chat_id in self.allowed_chats:
                return (True, chat_id)
            return (False, chat_id)
        return (False, 0)

    @only_allowed_chats_message
    async def start_command(self, message: Message, context: DEFAULT_CONTEXT):
        await message.reply_text('\n'.join(command_lines))

    @only_allowed_chats_message
    async def set_commands(self, message: Message, context: DEFAULT_CONTEXT):
        scope = BotCommandScopeChat(message.chat.id)
        await context.bot.set_my_commands(commands, scope)
        await message.reply_text('The commands have been set')

    @only_allowed_chats_message
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

    @staticmethod
    async def try_action(action: SERVERACTIONS, server_name: str):
        try:
            await Scaleway().perform_raw_action(f'{action}:{server_name}')
            return f'sended {action} action'
        except ValueError as error:
            return str(error)

    @staticmethod
    def get_server_name(context: DEFAULT_CONTEXT):
        return context.args[0] if context.args else None

    @only_allowed_chats_message
    async def poweron(self, message: Message, context: DEFAULT_CONTEXT):
        if server_name := self.get_server_name(context):
            msg = await self.try_action('poweron', server_name)
            await message.reply_text(msg)
        else:
            await self.ask_which_server(message, action='poweron')

    @only_allowed_chats_message
    async def poweroff(self, message: Message, context: DEFAULT_CONTEXT):
        if server_name := self.get_server_name(context):
            msg = await self.try_action('poweroff', server_name)
            await message.reply_text(msg)
        else:
            await self.ask_which_server(message, action='poweroff')

    @only_allowed_chats_callback
    async def ask_callback(self, callback_query: CallbackQuery):
        await callback_query.answer()
        data = callback_query.data
        if not data:
            await callback_query.edit_message_text('no data in callback_query')
            return
        try:
            action = await Scaleway().perform_raw_action(data)
            await callback_query.edit_message_text(f'sended {action} action')
        except ValueError as error:
            await callback_query.edit_message_text(str(error))
