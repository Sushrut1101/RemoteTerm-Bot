"""Run the Telegram bot with long polling."""

from __future__ import annotations

from remote_term_bot import logger
from remote_term_bot.bot import create_application
from remote_term_bot.config import Settings

def main() -> None:
    try:
        settings = Settings.from_environment()
        print(f"[{logger.ts()}] [INFO] Environment variables loaded...")
        application = create_application(settings)
    except (ValueError, OSError) as exc:
        logger.error(f"Configuration error: {exc}")
        raise SystemExit(2) from exc

    print(f"[{logger.ts()}] [INFO] Bot started...")
    application.run_polling(allowed_updates=["message"])

if __name__ == "__main__":
    main()
