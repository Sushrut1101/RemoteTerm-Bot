"""Telegram command handlers for RemoteTerm Bot."""

from __future__ import annotations

from telegram import Update
from telegram.constants import ParseMode
from telegram.ext import Application, CommandHandler, ContextTypes

from remote_term_bot.access import allowed
from remote_term_bot.config import Settings
from remote_term_bot.presentation import inline_code, session_details
from remote_term_bot.sessions import SessionManager, UptermError
from remote_term_bot import uptime
from remote_term_bot import logger

HELP_TEXT = (
    "RemoteTerm Bot commands:\n\n"
    "/start - welcome message\n"
    "/help - show this command list\n"
    "/new [0|1|2] - use the default mode or choose shell (0), tmux (1), or Byobu (2)\n"
    "/set <0|1|2> - set the default session mode\n"
    "/list - list your active sessions\n"
    "/show <id> - show SSH and session details\n"
    "/kill <id> - stop one session\n"
    "/killall - stop all active sessions\n"
    "/uptime - show the bot's uptime"
)

def _manager(context: ContextTypes.DEFAULT_TYPE) -> SessionManager:
    return context.application.bot_data["sessions"]

def _log(update: Update, command: str, response: str = "") -> None:
    user = update.effective_user
    logger.info(user.id if user else "SYSTEM", command, response)

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    await update.effective_message.reply_text(
        "Welcome to RemoteTerm Bot! Create and manage remote Upterm terminal sessions here.\n\n"
        "Use /help to see available commands."
    )
    _log(update, "/start")

async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    await update.effective_message.reply_text(HELP_TEXT)
    _log(update, "/help")

async def new_session(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    if not await allowed(update, context):
        return
    if len(context.args) > 1 or (context.args and context.args[0] not in {"0", "1", "2"}):
        await update.effective_message.reply_text(
            "Usage: /new [0|1|2]\n0 = shell (default)\n1 = tmux\n2 = Byobu"
        )
        _log(update, "/new", "Invalid usage")
        return
    await update.effective_message.reply_text("Starting an Upterm session…")

    try:
        mode = int(context.args[0]) if context.args else context.application.bot_data["default_mode"]
        session = await _manager(context).create(mode)
    except UptermError as exc:
        logger.error(f"Could not create Upterm session: {exc}")
        await update.effective_message.reply_text(f"Could not create session: {exc}")
        return

    await update.effective_message.reply_text(session_details(session), parse_mode=ParseMode.MARKDOWN_V2)
    _log(update, "/new", "Upterm session created")

async def set_default_mode(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    if not await allowed(update, context):
        return
    if len(context.args) != 1 or context.args[0] not in {"0", "1", "2"}:
        await update.effective_message.reply_text("Usage: /set <0|1|2>\n0 = shell\n1 = tmux\n2 = Byobu")
        _log(update, "/set", "Invalid usage")
        return

    mode = int(context.args[0])
    context.application.bot_data["default_mode"] = mode
    mode_name = {0: "shell", 1: "tmux", 2: "Byobu"}[mode]
    await update.effective_message.reply_text(
        f"Default session mode set to {mode_name} ({mode}). This setting lasts until the bot restarts."
    )
    _log(update, "/set", f"Default mode set to {mode_name} ({mode})")

async def show_uptime(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    if not await allowed(update, context):
        return
    message = f"⏱ Uptime: {inline_code(uptime.get_uptime())}"
    await update.effective_message.reply_text(message, parse_mode=ParseMode.MARKDOWN_V2)
    _log(update, "/uptime", "Uptime displayed")

async def list_sessions(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    if not await allowed(update, context):
        return
    sessions = await _manager(context).list_active()
    if not sessions:
        await update.effective_message.reply_text("There are no active sessions.")
        _log(update, "/list", "No active sessions")
        return
    text = "Active sessions:\n" + "\n".join(
        f"Session: {inline_code(session.session_id)} | Status: {inline_code(session.status)}"
        for session in sessions
    )
    await update.effective_message.reply_text(text, parse_mode=ParseMode.MARKDOWN_V2)
    _log(update, "/list", f"Displayed {len(sessions)} active session(s)")

async def show_session(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    if not await allowed(update, context):
        return
    if len(context.args) != 1:
        await update.effective_message.reply_text("Usage: /show <id>")
        _log(update, "/show", "Invalid usage")
        return
    session = await _manager(context).get(context.args[0])
    if session:
        await update.effective_message.reply_text(session_details(session), parse_mode=ParseMode.MARKDOWN_V2)
    else:
        await update.effective_message.reply_text("Session not found or no longer active.")
    _log(update, f"/show {context.args[0]}", "Displayed session details" if session else "Session not found")

async def kill_session(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    if not await allowed(update, context):
        return
    if len(context.args) != 1:
        await update.effective_message.reply_text("Usage: /kill <id>")
        _log(update, "/kill", "Invalid usage")
        return
    try:
        stopped = await _manager(context).stop(context.args[0])
    except UptermError as exc:
        logger.error(f"Could not stop Upterm session: {exc}")
        await update.effective_message.reply_text(f"Could not stop session: {exc}")
        return
    await update.effective_message.reply_text("Session stopped." if stopped else "Session not found or already ended.")
    _log(update, f"/kill {context.args[0]}", "Session stopped" if stopped else "Session not found")

async def kill_all(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    if not await allowed(update, context):
        return
    if context.args:
        await update.effective_message.reply_text("Usage: /killall")
        _log(update, "/killall", "Invalid usage")
        return
    try:
        stopped = await _manager(context).stop_all()
    except UptermError as exc:
        logger.error(f"Could not stop all Upterm sessions: {exc}")
        await update.effective_message.reply_text(f"Could not stop all sessions: {exc}")
        return
    await update.effective_message.reply_text(f"Stopped {stopped} active session(s).")
    _log(update, "/killall", f"Stopped {stopped} session(s)")

def create_application(settings: Settings) -> Application:
    application = Application.builder().token(settings.bot_token).build()
    application.bot_data["settings"] = settings
    application.bot_data["sessions"] = SessionManager("upterm")
    application.bot_data["default_mode"] = settings.default_mode

    for command, callback in (
        ("start", start),
        ("help", help_command),
        ("new", new_session),
        ("set", set_default_mode),
        ("uptime", show_uptime),
        ("list", list_sessions),
        ("show", show_session),
        ("kill", kill_session),
        ("killall", kill_all),
    ):
        application.add_handler(CommandHandler(command, callback))

    application.add_error_handler(_handle_error)
    return application

async def _handle_error(update: object, context: ContextTypes.DEFAULT_TYPE) -> None:
    error_type = type(context.error).__name__ if context.error is not None else "unknown"
    error_message = str(context.error) if context.error is not None else "No exception details"
    logger.error(f"Unhandled Telegram update error ({error_type}): {error_message}")
