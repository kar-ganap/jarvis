# Phase 7: Browser + Notion + Google Slides — Plan

See full plan at: `~/.claude/plans/sequential-fluttering-bear.md`

## Summary

Three new integrations following the existing HTTP bridge pattern:

- **Browser** (Playwright): `navigate`, `screenshot`, `extract` — 3 tools, 3 endpoints
- **Notion** (`notion-client`): `search`, `read_page`, `create_page`, `append_blocks`, `query_database` — 5 tools, 5 endpoints
- **Google Slides** (`googleapiclient`): `list`, `read`, `create`, `add_slide` — 4 tools, 4 endpoints

Total: 12 new tools (30 total), 12 new endpoints (26 total), ~36 new tests (168 total).

## Implementation Order

1. Sub-phase 7A: Google Slides (extends existing Google pattern)
2. Sub-phase 7B: Notion (new package, new module)
3. Sub-phase 7C: Browser Automation (Playwright lifecycle)
