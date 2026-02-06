from __future__ import annotations


def read_file(path: str) -> str:
    """Read the contents of a text file.

    Args:
        path: Absolute or relative path to the file.

    Returns:
        The file contents, or an error message if the file cannot be read.
    """
    import os

    if not os.path.isabs(path):
        path = os.path.join(os.path.expanduser("~"), path)

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
    import os

    if not os.path.isabs(path):
        path = os.path.join(os.path.expanduser("~"), path)

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
    import os

    path = os.path.expanduser(path)
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
