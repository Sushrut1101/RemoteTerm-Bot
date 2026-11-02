"""Process uptime formatting."""

import time

start_time = time.monotonic()

def get_uptime() -> str:
    elapsed = int(time.monotonic() - start_time)
    days, remainder = divmod(elapsed, 86_400)
    hours, remainder = divmod(remainder, 3_600)
    minutes, seconds = divmod(remainder, 60)
    return f"{days}d {hours}h {minutes}m {seconds}s"
