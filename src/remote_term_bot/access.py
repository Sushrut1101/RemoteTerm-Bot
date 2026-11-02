"""Access checks shared by all Telegram command handlers."""

from telegram import Update
from telegram.constants import ChatType
from telegram.ext import ContextTypes

from remote_term_bot.config import Settings
from remote_term_bot import logger

async def allowed(update: Update, context: ContextTypes.DEFAULT_TYPE) -> bool:
    settings: Settings = context.application.bot_data["settings"]
    user = update.effective_user
    message = update.effective_message
    if user is None or user.id not in settings.authorized_users or update.effective_chat is None:
        if user is not None:
            command = message.text.split(maxsplit=1)[0] if message and message.text else "unknown command"
            logger.deny(user.id, command)
        if message:
            await message.reply_text("⛔ You are not authorized to use this bot!")
        return False
    return True
