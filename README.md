# RemoteTerm Bot

A Telegram bot for creating and managing shared [Upterm](https://upterm.dev/) terminal sessions.

## Requirements

- Python 3.11 or newer
- [`uv`](https://docs.astral.sh/uv/)
- The [Upterm](https://upterm.dev/) CLI installed on the machine running the bot
- `tmux` installed for `/new 1`
- Byobu installed for `/new 2` (uses tmux as its backend)
- A Telegram bot token from [@BotFather](https://t.me/BotFather)

## Setup

```bash
uv sync
cp example.env .env
```

Create `.env` in the directory you launch the bot from, and set `BOT_TOKEN` and `AUTHORIZED_USERS`. `AUTHORIZED_USERS` is a comma-separated list of Telegram numeric user IDs. The bot only responds to those users and only in private chats.

```dotenv
BOT_TOKEN=your-telegram-bot-token
AUTHORIZED_USERS=123456789
```
Or, you can set `BOT_TOKEN` and `AUTHORIZED_USERS` env variables in your shell and export them before running the bot.

## Run

Run from the repository root:

```bash
uvx .
```
Or
```bash
uv run remote-term-bot
```

The bot starts `upterm host` in the background, accepts the session without an interactive prompt, skips host-key confirmation, and runs `$SHELL` (or `/bin/sh` when unset). It polls Upterm until the session is ready before reporting the connection details. Upterm's `--accept` mode allows anyone who has the session ID to join; share the SSH details only with intended participants. Session records are held in process memory and are cleared when the bot exits. After a restart, previously created sessions are no longer available to `/list`, `/show`, or `/kill`, even if an Upterm host process is still running.

The IDs shown by `/new` and `/list` are Upterm's own session IDs. The bot keeps Upterm's local session name internally to query and stop each session.

## Commands

| Command | Description |
| --- | --- |
| `/start` | Show the welcome message |
| `/help` | Show commands and usage |
| `/new [0|1|2]` | Start a shell session (`0`, default), tmux session (`1`), or Byobu session (`2`) |
| `/list` | List active sessions created by this bot |
| `/show <id>` | Show SSH and other connection details |
| `/kill <id>` | Stop a session |
| `/killall` | Stop all active sessions created by this bot |

## Project layout

```text
src/remote_term_bot/
├── access.py       # User and private-chat access checks
├── bot.py          # Telegram command handlers and application setup
├── config.py       # Environment-based settings
├── presentation.py # Telegram formatting for session details
├── sessions.py     # Upterm CLI integration and in-memory session tracking
└── __main__.py     # Application entry point
```
