# Phase 7 Retro: Browser + Notion + Google Slides

## What was delivered

Three new integrations following the established HTTP bridge pattern:

- **Google Slides** (4 tools): list, read, create, add_slide. Reuses existing Google OAuth with 2 new scopes (`presentations`, `drive.readonly`).
- **Notion** (5 tools): search, read_page, create_page, append_blocks, query_database. Uses `notion-client` SDK with internal integration token.
- **Browser** (3 tools): navigate, screenshot, extract. Playwright with lazy-init headless Chromium singleton.

**Totals**: 30 tools, 26 HTTP endpoints, 168 tests (152 unit + 16 integration).

## Files created (13)

- `src/jarvis/browser/__init__.py`, `src/jarvis/browser/handlers.py`
- `src/jarvis/tools/browser.py`
- `src/jarvis/notion/__init__.py`, `src/jarvis/notion/handlers.py`
- `src/jarvis/tools/notion.py`
- `src/jarvis/google/slides_handlers.py`
- `src/jarvis/tools/gslides.py`
- `tests/unit/test_browser_handlers.py`, `tests/unit/test_browser_tool.py`
- `tests/unit/test_notion_handlers.py`, `tests/unit/test_notion_tool.py`
- `tests/unit/test_slides_handlers.py`, `tests/unit/test_gslides_tool.py`
- `tests/integration/test_notion_roundtrip.py`

## Files modified (9)

- `src/jarvis/http_server.py` — 12 new endpoints
- `src/jarvis/agent/factory.py` — wired 3 new tool modules
- `src/jarvis/agent/persona.py` — added BROWSER, NOTION, GOOGLE SLIDES sections
- `src/jarvis/settings.py` — added BrowserSettings, NotionSettings
- `src/jarvis/google/auth.py` — added presentations + drive.readonly scopes
- `scripts/setup_google_oauth.py` — same scopes
- `tests/unit/test_http_server.py` — 6 new endpoint tests, fixture expansion
- `tests/unit/test_settings.py` — 2 new settings tests
- `config/jarvis.yaml`, `.env.example`

## Live validation

### Browser (all passing)

| Tool | Input | Result |
|---|---|---|
| `browser_navigate` | `https://example.com` | Title: "Example Domain", 129 chars text |
| `browser_screenshot` | `https://example.com` | 16KB PNG rendered correctly |
| `browser_extract` | `https://example.com`, `h1` | "Example Domain", 1 element |

### Notion (all passing)

| Tool | Input | Result |
|---|---|---|
| `notion_search` | `''` | Found 1 shared page ("Shashank <> Kartik") |
| `notion_read_page` | shared page ID | Title + content returned correctly |
| `notion_create_page` | child of shared page | "Jarvis Test Page" created with URL |
| `notion_append_blocks` | 2 paragraphs | 2 blocks appended |
| Read-back | new page ID | Content matches exactly what was written |

### Google Slides (deferred)

User's Google account has issues — Slides live validation deferred. Unit tests (4) passing with mocked API.

## What went well

- HTTP bridge pattern is now battle-tested across 5 domains (scheduler, Gmail, GCal, Slides, Notion, Browser). Adding a new integration is mechanical.
- TDD discipline caught a real bug: Notion `_extract_title` needed `prop.get("type") == "title"` check, and mock data missing this key exposed it immediately.
- Sub-phase ordering (Slides first, then Notion, then Browser) was correct — Slides was simplest (extends existing Google pattern), Browser was most complex (lazy singleton lifecycle).

## What could be better

- Integration conftest `pytest_collection_modifyitems` was applying skip markers to ALL collected items, not just integration tests. Running `pytest tests/` silently skipped everything — dangerous because CI would show green with zero tests executed. Fixed: now filters by path so only `tests/integration/` items get skipped.
- Playwright mock chain (`sync_playwright().start()`) was misaligned in initial RED tests — `mock_sync(return_value=mock_pw)` didn't account for the `.start()` intermediate call. Fixed during GREEN phase by introducing `mock_cm` with `mock_cm.start.return_value = mock_pw`.
- The `test_http_server.py` fixture grows with every new handler module. All WhatsApp standalone fixtures must also patch every new import. Consider refactoring to a shared patch context in a future phase.

## Remaining manual steps

- [ ] Re-run `scripts/setup_google_oauth.py` to grant Slides + Drive scopes (when Google account is fixed)
- [ ] Live test `gslides_list()` returns Drive presentations
