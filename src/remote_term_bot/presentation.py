"""Format session data for Telegram messages."""

from remote_term_bot.sessions import Session

def session_details(session: Session) -> str:
    lines = [f"Session: {session.session_id}", f"Status: {session.status}"]

    if session.ssh_command:
        lines.append(f"SSH: {session.ssh_command}")
    if session.join_url:
        lines.append(f"Join: {session.join_url}")
    if session.sftp_command:
        lines.append(f"SFTP: {session.sftp_command}")
    if session.scp_command:
        lines.extend(session.scp_command.splitlines())

    return "\n".join(lines)
