from __future__ import annotations


def gsheets_list(max_results: int = 10) -> str:
    """List Google Sheets spreadsheets.

    Args:
        max_results: Maximum number of spreadsheets to return.

    Returns:
        Formatted list of spreadsheets with IDs and names.
    """
    import os

    import requests

    port = os.environ.get("JARVIS_HTTP_PORT", "9100")
    host = os.environ.get("JARVIS_HTTP_HOST", "host.docker.internal")
    resp = requests.post(
        f"http://{host}:{port}/google/sheets/list",
        json={"max_results": max_results},
        timeout=30,
    )
    resp.raise_for_status()
    data = resp.json()
    results = data.get("results", [])
    if not results:
        return "No spreadsheets found."
    lines = []
    for r in results:
        name = r.get("name", "(untitled)")
        modified = r.get("modified", "")
        lines.append(f"  [{r['id']}] {name} — modified {modified}")
    return f"Found {len(results)} spreadsheets:\n" + "\n".join(lines)


def gsheets_read(spreadsheet_id: str, range_str: str = "Sheet1") -> str:
    """Read values from a Google Sheets range.

    Args:
        spreadsheet_id: The spreadsheet ID to read.
        range_str: The range to read (e.g. 'Sheet1!A1:C10').

    Returns:
        Formatted table of values from the range.
    """
    import os

    import requests

    port = os.environ.get("JARVIS_HTTP_PORT", "9100")
    host = os.environ.get("JARVIS_HTTP_HOST", "host.docker.internal")
    resp = requests.post(
        f"http://{host}:{port}/google/sheets/read",
        json={"spreadsheet_id": spreadsheet_id, "range_str": range_str},
        timeout=30,
    )
    resp.raise_for_status()
    data = resp.json()
    values = data.get("values", [])
    if not values:
        return f"Spreadsheet {spreadsheet_id} range {range_str}: (empty)"
    lines = [f"Range: {data.get('range', range_str)}"]
    for row in values:
        lines.append("  " + " | ".join(str(cell) for cell in row))
    return "\n".join(lines)


def gsheets_create(title: str) -> str:
    """Create a new Google Sheets spreadsheet.

    Args:
        title: Title for the new spreadsheet.

    Returns:
        Confirmation with spreadsheet ID.
    """
    import os

    import requests

    port = os.environ.get("JARVIS_HTTP_PORT", "9100")
    host = os.environ.get("JARVIS_HTTP_HOST", "host.docker.internal")
    resp = requests.post(
        f"http://{host}:{port}/google/sheets/create",
        json={"title": title},
        timeout=30,
    )
    resp.raise_for_status()
    data = resp.json()
    return f"Created spreadsheet '{data.get('title', title)}' (id: {data.get('id', 'unknown')})"


def gsheets_append(
    spreadsheet_id: str, range_str: str, values_json: str,
) -> str:
    """Append rows to a Google Sheets spreadsheet.

    Args:
        spreadsheet_id: The spreadsheet ID to append to.
        range_str: The target range (e.g. 'Sheet1').
        values_json: JSON-encoded list of lists, e.g. '[["A", "B"], ["C", "D"]]'.

    Returns:
        Confirmation with number of rows appended.
    """
    import os

    import requests

    port = os.environ.get("JARVIS_HTTP_PORT", "9100")
    host = os.environ.get("JARVIS_HTTP_HOST", "host.docker.internal")
    resp = requests.post(
        f"http://{host}:{port}/google/sheets/append",
        json={
            "spreadsheet_id": spreadsheet_id,
            "range_str": range_str,
            "values_json": values_json,
        },
        timeout=30,
    )
    resp.raise_for_status()
    data = resp.json()
    return f"Appended {data.get('updated_rows', 0)} rows to spreadsheet {spreadsheet_id}"


TOOLS = [gsheets_list, gsheets_read, gsheets_create, gsheets_append]
