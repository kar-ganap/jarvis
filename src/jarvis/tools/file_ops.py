from __future__ import annotations

import os
from pathlib import Path


def _validate_path(path: str) -> str | None:
    """Resolve path and verify it's under the home directory.

    Returns the resolved path string, or None if outside home.
    """
    home = Path(os.path.expanduser("~")).resolve()
    if os.path.isabs(path):
        resolved = Path(path).resolve()
    else:
        resolved = (home / path).resolve()
    if not str(resolved).startswith(str(home)):
        return None
    return str(resolved)


def read_file(path: str) -> str:
    """Read the contents of a text file.

    Args:
        path: Absolute or relative path to the file.

    Returns:
        The file contents, or an error message if the file cannot be read.
    """
    safe_path = _validate_path(path)
    if safe_path is None:
        return f"BLOCKED: Path outside home directory: {path}"
    path = safe_path

    if not os.path.exists(path):
        return f"ERROR: File not found: {path}"

    with open(path) as f:
        content = f.read()

    if len(content) > 10000:
        return content[:10000] + f"\n\n[TRUNCATED — file is {len(content)} chars total]"
    return content


def write_file(path: str, content: str) -> str:
    """Write content to a text file. Creates parent directories if needed.

    Args:
        path: Absolute or relative path to the file.
        content: The text content to write.

    Returns:
        A confirmation message or error.
    """
    safe_path = _validate_path(path)
    if safe_path is None:
        return f"BLOCKED: Path outside home directory: {path}"
    path = safe_path

    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "w") as f:
        f.write(content)

    return f"OK: Wrote {len(content)} chars to {path}"


def list_directory(path: str = "~") -> str:
    """List the contents of a directory.

    Args:
        path: Directory path. Defaults to home directory.

    Returns:
        A formatted listing of files and directories.
    """
    safe_path = _validate_path(path)
    if safe_path is None:
        return f"BLOCKED: Path outside home directory: {path}"
    path = safe_path

    if not os.path.isdir(path):
        return f"ERROR: Not a directory: {path}"

    entries = sorted(os.listdir(path))
    lines = []
    for entry in entries[:100]:
        full = os.path.join(path, entry)
        suffix = "/" if os.path.isdir(full) else ""
        lines.append(f"  {entry}{suffix}")

    header = f"Contents of {path} ({len(entries)} items):"
    if len(entries) > 100:
        lines.append(f"  ... and {len(entries) - 100} more")
    return header + "\n" + "\n".join(lines)


TOOLS = [read_file, write_file, list_directory]
