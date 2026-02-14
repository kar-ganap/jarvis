from __future__ import annotations

import re

import structlog

_log = structlog.get_logger()

_BLOCKED_PATTERNS = [
    r"\brm\s+(-[a-zA-Z]*r|-[a-zA-Z]*f)+",
    r"\bmkfs\b",
    r"\bdd\s+.*of=/dev/",
    r":\(\)\s*\{",
    r">\s*/dev/[sh]d",
    r"\bchmod\s+777\s+/",
    r"\bshutdown\b",
    r"\breboot\b",
]


def _is_blocked(command: str) -> bool:
    """Check if command matches any blocked pattern."""
    for pattern in _BLOCKED_PATTERNS:
        if re.search(pattern, command):
            return True
    return False


def execute_shell_command(command: str, workdir: str = "") -> str:
    """Execute a shell command and return the output.

    Args:
        command: The shell command to execute.
        workdir: Working directory. Defaults to home directory if empty.

    Returns:
        A string with stdout, stderr, and exit code.
    """
    import os
    import subprocess

    workdir = workdir or os.path.expanduser("~")

    if _is_blocked(command):
        _log.warning("shell.command_blocked", command=command)
        return f"BLOCKED: Command rejected by safety filter: {command}"

    # Filter sensitive env vars
    env = {
        k: v
        for k, v in os.environ.items()
        if not any(
            secret in k.upper()
            for secret in ("KEY", "SECRET", "TOKEN", "PASSWORD", "CREDENTIAL")
        )
    }

    try:
        result = subprocess.run(
            command,
            shell=True,
            capture_output=True,
            text=True,
            timeout=30,
            cwd=workdir,
            env=env,
        )
    except subprocess.TimeoutExpired:
        return f"ERROR: Command timed out after 30 seconds: {command}"

    parts = []
    if result.stdout:
        parts.append(f"STDOUT:\n{result.stdout}")
    if result.stderr:
        parts.append(f"STDERR:\n{result.stderr}")
    parts.append(f"EXIT CODE: {result.returncode}")
    return "\n".join(parts)


TOOLS = [execute_shell_command]
