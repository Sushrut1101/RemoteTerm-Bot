"""Manage Upterm processes and in-memory session records."""

from __future__ import annotations

import asyncio
import json
import os
import secrets
import time
from dataclasses import dataclass
from typing import Any

class UptermError(RuntimeError):
    """Raised when the Upterm CLI cannot complete an operation."""

@dataclass(frozen=True, slots=True)
class Session:
    session_id: str
    name: str
    status: str
    ssh_command: str
    join_url: str
    command: str = ""
    force_command: str = ""
    sftp_command: str = ""
    scp_command: str = ""

class SessionManager:
    def __init__(self, binary: str) -> None:
        self.binary = binary
        self._sessions: dict[str, Session] = {}
        self._host_processes: dict[str, asyncio.subprocess.Process] = {}
        self._process_output: dict[str, bytearray] = {}
        self._output_readers: dict[str, asyncio.Task[None]] = {}

    async def _run(self, *arguments: str, timeout: float = 45) -> tuple[int, str, str]:
        try:
            process = await asyncio.create_subprocess_exec(
                self.binary,
                *arguments,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE,
            )
        except FileNotFoundError as exc:
            raise UptermError(f"Upterm executable not found: {self.binary}") from exc
        try:
            stdout, stderr = await asyncio.wait_for(process.communicate(), timeout=timeout)
        except TimeoutError as exc:
            process.kill()
            await process.wait()
            raise UptermError("Upterm did not respond in time.") from exc
        return process.returncode or 0, stdout.decode(errors="replace").strip(), stderr.decode(errors="replace").strip()

    async def create(self) -> Session:
        session_name = f"remote-term-{secrets.token_hex(4)}"

        try:
            process = await asyncio.create_subprocess_exec(
                self.binary,
                "host",
                "--accept",
                "--skip-host-key-check",
                "--name",
                session_name,
                "--",
                os.getenv("SHELL") or "/bin/sh",
                stdin=asyncio.subprocess.DEVNULL,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.STDOUT,
                start_new_session=True,
            )
        except FileNotFoundError as exc:
            raise UptermError(f"Upterm executable not found: {self.binary}") from exc

        self._host_processes[session_name] = process
        self._process_output[session_name] = bytearray()
        self._output_readers[session_name] = asyncio.create_task(self._capture_output(session_name, process))
        deadline = time.monotonic() + 45

        while time.monotonic() < deadline:
            if process.returncode is not None:
                break
            code, output, _ = await self._run("session", "info", session_name, "-o", "json", timeout=5)
            if code == 0:
                try:
                    details = json.loads(output)
                except json.JSONDecodeError:
                    details = {}
                if details.get("status") == "ready":
                    session = self._from_details(session_name, details)
                    self._sessions[session.session_id] = session
                    return session
            await asyncio.sleep(1)
        if process.returncode is None:
            process.terminate()
        await process.wait()
        await self._forget_process(session_name)
        log_output = bytes(self._process_output.pop(session_name, bytearray())).decode(errors="replace")[-3000:]

        raise UptermError(log_output.strip() or "Upterm exited before the session became ready.")

    async def _capture_output(self, session_id: str, process: asyncio.subprocess.Process) -> None:
        if process.stdout is None:
            return
        output = self._process_output[session_id]
        while chunk := await process.stdout.read(4096):
            output.extend(chunk)
            if len(output) > 8192:
                del output[:-8192]

    async def _forget_process(self, session_id: str) -> None:
        self._host_processes.pop(session_id, None)
        reader = self._output_readers.pop(session_id, None)
        if reader is not None:
            await reader

    @staticmethod
    def _from_details(session_id: str, data: dict[str, Any]) -> Session:
        ssh_command = str(data.get("sshCommand", ""))
        target = ssh_command.removeprefix("ssh ").strip() if ssh_command.startswith("ssh ") else ""
        upstream_id = str(data.get("sessionId") or (target.split("@", 1)[0] if "@" in target else session_id))
        session_name = str(data.get("name") or session_id)
        join_command = str(
            data.get("joinCommand")
            or data.get("joinUrl")
            or data.get("join")
            or (f"upterm join ssh://{target}" if target else "")
        )
        access = str(data.get("access", ""))
        if not access and data.get("open") is True:
            access = "open: anyone with the session ID can join"

        return Session(
            session_id=upstream_id,
            name=session_name,
            status=str(data.get("status", "ready")),
            ssh_command=ssh_command,
            join_url=join_command,
            command=str(data.get("command", "")),
            force_command=str(data.get("forceCommand", "")),
            sftp_command=str(data.get("sftpCommand") or (f"sftp {target}" if target else "")),
            scp_command=(
                f"SCP to: scp <local> {target}:<remote>\n"
                f"SCP from: scp {target}:<remote> <local>"
                if target
                else str(data.get("scpCommand", ""))
            ),
        )

    async def _refresh(self, session_id: str) -> Session | None:
        if session_id not in self._sessions:
            return None
        previous = self._sessions[session_id]
        code, output, _ = await self._run("session", "info", previous.name, "-o", "json")
        if code:
            self._sessions.pop(session_id, None)
            return None
        try:
            data = json.loads(output)
        except json.JSONDecodeError:
            self._sessions.pop(session_id, None)
            return None
        session = self._from_details(previous.name, data)
        if session.status in {"ended", "stopped", "failed", "startup_failed"}:
            self._sessions.pop(session_id, None)
            return None
        self._sessions.pop(session_id, None)
        self._sessions[session.session_id] = session

        return session

    async def list_active(self) -> list[Session]:
        ids = list(self._sessions)
        sessions = await asyncio.gather(*(self._refresh(session_id) for session_id in ids))
        active = [session for session in sessions if session is not None]
        active.sort(key=lambda session: session.session_id)
        return active

    async def get(self, session_id: str) -> Session | None:
        return await self._refresh(session_id) if session_id in self._sessions else None

    async def stop(self, session_id: str) -> bool:
        session = await self.get(session_id)
        if session is None:
            return False
        code, output, error = await self._run("session", "stop", session.name)
        if code:
            raise UptermError(error or output or f"Could not stop session {session_id}.")
        host_process = self._host_processes.get(session.name)
        if host_process is not None and host_process.returncode is None:
            try:
                await asyncio.wait_for(host_process.wait(), timeout=5)
            except TimeoutError:
                host_process.terminate()
                await host_process.wait()
        await self._forget_process(session.name)
        self._process_output.pop(session.name, None)
        self._sessions.pop(session_id, None)
        return True

    async def stop_all(self) -> int:
        sessions = await self.list_active()
        stopped = 0
        for session in sessions:
            if await self.stop(session.session_id):
                stopped += 1
        return stopped
