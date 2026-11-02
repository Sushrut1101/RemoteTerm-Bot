"""Small timestamped console logger for bot events."""

from __future__ import annotations

from datetime import datetime

def ts() -> str:
    return datetime.now().strftime("%d-%m-%Y %H:%M:%S")

def info(user_id: int | str, command: str, response: str = "") -> None:
    print(f"[{ts()}] [INFO] {user_id} - Used {command}", flush=True)
    if response:
        for line in response.strip().splitlines():
            print(f"           {line}", flush=True)

def deny(user_id: int | str, command: str) -> None:
    print(f"[{ts()}] [DENY] [UNAUTHORIZED] {user_id} tried {command}", flush=True)

def warning(message: str) -> None:
    print(f"[{ts()}] [WARN] {message}", flush=True)

def error(message: str) -> None:
    print(f"[{ts()}] [ERROR] {message}", flush=True)
