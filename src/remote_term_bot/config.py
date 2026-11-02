"""Application settings loaded from the environment."""

from __future__ import annotations

import os
from dataclasses import dataclass
from pathlib import Path
from dotenv import load_dotenv

@dataclass(frozen=True, slots=True)
class Settings:
    bot_token: str
    authorized_users: frozenset[int]
    default_mode: int

    @classmethod
    def from_environment(cls) -> "Settings":
        load_dotenv(dotenv_path=Path.cwd() / ".env")

        token = os.getenv("BOT_TOKEN", "").strip()
        if not token:
            raise ValueError("BOT_TOKEN is required. Add it to .env or the environment.")

        raw_users = os.getenv("AUTHORIZED_USERS", "").strip()
        if not raw_users:
            raise ValueError("AUTHORIZED_USERS must contain at least one Telegram user ID.")
        try:
            users = frozenset(int(value.strip()) for value in raw_users.split(",") if value.strip())
        except ValueError as exc:
            raise ValueError("AUTHORIZED_USERS must be comma-separated numeric Telegram user IDs.") from exc
        if not users:
            raise ValueError("AUTHORIZED_USERS must contain at least one Telegram user ID.")

        raw_mode = os.getenv("DEFAULT_MODE", "0").strip() or "0"
        try:
            default_mode = int(raw_mode)
        except ValueError as exc:
            raise ValueError("DEFAULT_MODE must be 0 (shell), 1 (tmux), or 2 (Byobu).") from exc
        if default_mode not in {0, 1, 2}:
            raise ValueError("DEFAULT_MODE must be 0 (shell), 1 (tmux), or 2 (Byobu).")

        return cls(
            bot_token=token,
            authorized_users=users,
            default_mode=default_mode,
        )
