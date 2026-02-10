# Phase 9 Retrospective — Google Docs/Sheets + Todoist + Memory & Learning

## Delivered

### 9A: Todoist Integration
- 4 Letta tools: `todoist_list_tasks`, `todoist_create_task`, `todoist_complete_task`, `todoist_list_projects`
- 4 HTTP endpoints: `/todoist/tasks`, `/todoist/tasks/create`, `/todoist/tasks/complete`, `/todoist/projects`
- `TodoistSettings` in settings with `TODOIST_API_KEY` env var fallback
- REST API v2 via `requests` — no SDK needed
- Live-validated: list projects (2), list tasks (15), create + complete round-trip

### 9B: Google Docs
- 4 Letta tools: `gdocs_list`, `gdocs_read`, `gdocs_create`, `gdocs_append`
- 4 HTTP endpoints: `/google/docs/list`, `/google/docs/read`, `/google/docs/create`, `/google/docs/append`
- Text extraction from nested `body.content` paragraph elements
- Append via `batchUpdate` with `insertText` at `endOfSegmentLocation`
- Added `documents` + `spreadsheets` scopes together (single re-auth for 9B+9C)
- Live-validated: create doc, append text, read back content

### 9C: Google Sheets
- 4 Letta tools: `gsheets_list`, `gsheets_read`, `gsheets_create`, `gsheets_append`
- 4 HTTP endpoints: `/google/sheets/list`, `/google/sheets/read`, `/google/sheets/create`, `/google/sheets/append`
- `values_json: str` param for write data (JSON-encoded `list[list]` to work around Letta's primitive-type constraint)
- Live-validated: create sheet, append 3 rows, read values back correctly

### 9D: Memory & Learning
- 2 Letta tools: `save_note`, `recall_notes`
- 2 HTTP endpoints: `/memory/save`, `/memory/recall`
- Archival memory using `passages` API with tag-based categories (not text prefix)
- Learning module: reads Prometheus counters → builds usage summary → updates human memory block
- Cron-scheduled via `SchedulerEngine.add_cron()` in `app.py`
- `MemorySettings` with `learning_enabled` and `learning_interval_hours`
- Live-validated against real Letta server: save, recall, stats collection, block update, full cycle

## Numbers

| Metric | Phase 8 | Phase 9 | Delta |
|--------|---------|---------|-------|
| Letta tools | 30 | 44 | +14 |
| HTTP endpoints | 28 | 42 | +14 |
| Unit tests | 187 | 218 | +31 |
| Integration tests | 16 | 16 | +0 |
| Total tests | 203 | 234 | +31 |

## What Went Well

- **TDD rhythm**: RED → GREEN cycle worked cleanly for all 4 sub-phases.
- **Pattern reuse**: Google Docs and Sheets handlers followed the exact same pattern as Slides — Drive API for listing, service-specific API for CRUD.
- **Scopes batching**: Adding both Docs and Sheets OAuth scopes in 9B avoided double re-auth.
- **Prometheus counter reading**: `collect()` → `samples` API is clean and doesn't require external storage.
- **All 4 integrations live-validated** against real services, not just mocks.

## What Could Be Better

- **Google token re-auth**: Adding new scopes requires manual deletion of `google_token.json` + re-running setup. No automated migration.
- **Learning module is basic**: Only reads counters that reset on restart. Persistent usage history would be more useful long-term.
- **Letta SDK API changed**: `archival_memory` → `passages` API. Had to discover and fix during live validation. Better to check SDK docs/source upfront.

## Gotchas Discovered

- **Google API enablement**: OAuth scopes ≠ API enabled. Must enable each API (Docs, Sheets) separately in GCP console. First call returns 403 until enabled.
- **Letta `passages` API**: `archival_memory.insert/list` is gone. Now `passages.create(text=, tags=)` and `passages.search(query=, top_k=)`. Search returns `PassageSearchResponse.results` with `.content` (not `.text`) and `.timestamp` (not `.created_at`).
- **Letta `agents.blocks.list()` pagination**: Returns `SyncArrayPage`, not a list. Need `.items` guard.
- **Todoist `due` field**: Can be `null`, a string, or a dict. Must handle all cases.
- **Prometheus counter test state**: Global registry shared across tests. Learning cycle tests need explicit counter increments.
