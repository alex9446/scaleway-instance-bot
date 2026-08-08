from telegram import Chat, Update
from telegram.ext import ContextTypes


class Commands:
    def __init__(self, allowed_chats: list[int]):
        self.allowed_chats = allowed_chats

    def check_chat(self, chat: Chat):
        if chat.id not in self.allowed_chats:
            raise PermissionError(f'chat {chat.id} not allowed')

    async def start_command(self,
                            update: Update,
                            context: ContextTypes.DEFAULT_TYPE):
        if message := update.message:
            self.check_chat(message.chat)
            await message.reply_text('Hello!')
