"""Format session data for Telegram messages."""

from remote_term_bot.sessions import Session


def escape_markdown(value: str) -> str:
    special_characters = set(r"_*[]()~`>#+-=|{}.!\\")
    return "".join(f"\\{character}" if character in special_characters else character for character in value)


def inline_code(value: str) -> str:
    escaped = value.replace("\\", "\\\\").replace("`", "\\`")
    return f"`{escaped}`"

def session_details(session: Session) -> str:
    summary = [
        f"Session: {inline_code(session.session_id)}",
        f"Mode: {session.mode}",
        f"Status: {session.status}",
        f"Created by: {escape_markdown(session.created_by)}",
    ]
    connections: list[str] = []

    if session.ssh_command:
        connections.append(f"SSH: {inline_code(session.ssh_command)}")
    if session.join_url:
        connections.append(f"Join: {inline_code(session.join_url)}")
    if session.sftp_command:
        connections.append(f"SFTP: {inline_code(session.sftp_command)}")
    if session.scp_command:
        for line in session.scp_command.splitlines():
            label, separator, value = line.partition(":")
            if separator:
                connections.append(f"{label}: {inline_code(value.strip())}")
            else:
                connections.append(inline_code(line))

    if not connections:
        return "\n".join(summary)
    return "\n".join(summary) + "\n\n" + "\n".join(connections)
