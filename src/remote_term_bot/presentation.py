"""Format session data for Telegram messages."""

from remote_term_bot.sessions import Session

def inline_code(value: str) -> str:
    escaped = value.replace("\\", "\\\\").replace("`", "\\`")
    return f"`{escaped}`"

def session_details(session: Session) -> str:
    fields = [("Session", session.session_id), ("Status", session.status)]

    if session.ssh_command:
        fields.append(("SSH", session.ssh_command))
    if session.join_url:
        fields.append(("Join", session.join_url))
    if session.sftp_command:
        fields.append(("SFTP", session.sftp_command))
    if session.scp_command:
        for line in session.scp_command.splitlines():
            label, separator, value = line.partition(":")
            fields.append((label, value.strip() if separator else line))

    return "\n".join(f"{label}: {inline_code(value) if label != "Status" else value + "\n"}" for label, value in fields)
