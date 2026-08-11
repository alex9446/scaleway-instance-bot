from telegram import Chat, Update, BotCommand
from telegram.ext import ContextTypes

DEFAULT_CONTEXT = ContextTypes.DEFAULT_TYPE

commands = [
    BotCommand('start', 'print list of commands'),
    BotCommand('help', 'print list of commands'),
    BotCommand('set_commands', 'set commands menu')
]
commands_list = [f'/{cmd.command} - {cmd.description}' for cmd in commands]


class Commands:
    def __init__(self, allowed_chats: list[int]):
        self.allowed_chats = allowed_chats

    def check_chat(self, chat: Chat):
        if chat.id not in self.allowed_chats:
            raise PermissionError(f'chat {chat.id} not allowed')

    async def start_command(self, update: Update, context: DEFAULT_CONTEXT):
        if message := update.message:
            self.check_chat(message.chat)
            await message.reply_text('\n'.join(commands_list))

    async def set_commands(self, update: Update, context: DEFAULT_CONTEXT):
        if message := update.message:
            self.check_chat(message.chat)
            await context.bot.set_my_commands(commands)
            await message.reply_text('The commands have been set')
