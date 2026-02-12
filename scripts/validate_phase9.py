"""Phase 9 live validation — Google Docs + Google Sheets.

Usage:
  set -a && source ~/.zshrc && set +a
  uv run python scripts/validate_phase9.py
"""
from __future__ import annotations

import json
import os
import sys

token_path = os.environ.get("GOOGLE_TOKEN_PATH", "google_token.json")
if not os.path.exists(token_path):
    print(f"ERROR: Google token not found at {token_path}")
    print("Run: uv run python scripts/setup_google_oauth.py")
    sys.exit(1)


def validate_gdocs():
    """Validate Google Docs handlers."""
    from jarvis.google.docs_handlers import (
        gdocs_append,
        gdocs_create,
        gdocs_list,
        gdocs_read,
    )

    print("=== Google Docs Validation ===")

    # 1. List docs
    print("\n1. Listing docs...")
    docs = gdocs_list(max_results=3)
    print(f"   Found {len(docs)} docs")
    for d in docs:
        print(f"   - {d['name']} ({d['id'][:20]}...)")

    # 2. Create a doc
    print("\n2. Creating test doc...")
    new_doc = gdocs_create(title="Phase 9 Test Doc")
    doc_id = new_doc["id"]
    print(f"   Created: {new_doc['title']} (id={doc_id[:20]}...)")

    # 3. Read the doc (should be empty)
    print("\n3. Reading empty doc...")
    read_result = gdocs_read(doc_id)
    print(f"   Title: {read_result['title']}")
    print(f"   Text: '{read_result['content']}'")

    # 4. Append text
    print("\n4. Appending text...")
    append_result = gdocs_append(doc_id, "Hello from Phase 9 validation!")
    print(f"   Status: {append_result['status']}")

    # 5. Read again to verify append
    print("\n5. Reading after append...")
    read_result2 = gdocs_read(doc_id)
    print(f"   Text: '{read_result2['content']}'")

    print("\n   Google Docs: ALL PASS")
    return doc_id


def validate_gsheets():
    """Validate Google Sheets handlers."""
    from jarvis.google.sheets_handlers import (
        gsheets_append,
        gsheets_create,
        gsheets_list,
        gsheets_read,
    )

    print("\n=== Google Sheets Validation ===")

    # 1. List sheets
    print("\n1. Listing sheets...")
    sheets = gsheets_list(max_results=3)
    print(f"   Found {len(sheets)} sheets")
    for s in sheets:
        print(f"   - {s['name']} ({s['id'][:20]}...)")

    # 2. Create a sheet
    print("\n2. Creating test sheet...")
    new_sheet = gsheets_create(title="Phase 9 Test Sheet")
    sheet_id = new_sheet["id"]
    print(f"   Created: {new_sheet['title']} (id={sheet_id[:20]}...)")

    # 3. Append rows
    print("\n3. Appending rows...")
    values = [["Name", "Score"], ["Alice", "95"], ["Bob", "87"]]
    append_result = gsheets_append(sheet_id, "Sheet1", json.dumps(values))
    print(f"   Updated range: {append_result.get('updated_range', 'n/a')}")
    print(f"   Updated rows: {append_result.get('updated_rows', 'n/a')}")

    # 4. Read back
    print("\n4. Reading sheet...")
    read_result = gsheets_read(sheet_id, range_str="Sheet1")
    print(f"   Range: {read_result['range']}")
    print(f"   Values: {read_result['values']}")

    print("\n   Google Sheets: ALL PASS")
    return sheet_id


if __name__ == "__main__":
    try:
        doc_id = validate_gdocs()
        sheet_id = validate_gsheets()
        print("\n=== Phase 9 Live Validation COMPLETE ===")
        print(f"Test doc ID: {doc_id}")
        print(f"Test sheet ID: {sheet_id}")
    except Exception as e:
        print(f"\nFAILED: {e}")
        import traceback

        traceback.print_exc()
        sys.exit(1)
