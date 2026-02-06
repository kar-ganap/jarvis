from __future__ import annotations


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
