# Phase 11 Retrospective: Security Hardening + Public Repo Polish

## What was delivered

### Security Hardening (11A–11G)
- **11A**: HTTP Bearer Token Auth — `@web.middleware` on all 42 endpoints, `/health` and `/metrics` exempt. Configured via `auth_token` in YAML or `JARVIS_HTTP_AUTH_TOKEN` env var.
- **11B**: Shell Command Safety — Regex blocklist rejects `rm -rf`, fork bombs, device writes, `mkfs`, `shutdown`, `reboot`, `chmod 777 /`.
- **11C**: WhatsApp Sender Allowlist — `allowed_senders` list in config + `WHATSAPP_ALLOWED_SENDERS` env var. Empty = allow all.
- **11D**: File Path Sandboxing — `_validate_path()` resolves and jails all file ops to `$HOME`. Blocks absolute paths outside home and traversal attacks.
- **11E**: Browser URL Validation — `_validate_url()` blocks non-HTTP schemes and private/internal hosts (localhost, 127.0.0.1, 169.254.169.254, 10.*, 172.16-31.*, 192.168.*).
- **11F**: Docker Compose hardening (removed exposed DB port), aiohttp `client_max_size=2MB`, WhatsApp audio base64 cap at ~5MB.
- **11G**: Graceful shutdown — SIGTERM handler calls `app.stop()` via event loop.

### Public Repo Polish (11H)
- `LICENSE` (MIT)
- `scripts/demo.sh` — Interactive CLI walkthrough (19 prompts covering all tool categories)
- `.env.example` updated with security env vars
- `README.md` updated with security section and test counts
- `CLAUDE.md` updated to Phase 11 state
- Both YAML configs updated with `auth_token` and `allowed_senders`

## Test results

- **287 unit tests passing** (267 baseline + 20 new)
- **16 integration tests** (skipped without Letta server)
- **303 total**
- Ruff: clean
- mypy: clean (strict)

## New test breakdown

| Sub-phase | Tests | File |
|-----------|-------|------|
| 11A | 5 | `test_http_server.py::TestAuthMiddleware` |
| 11B | 4 | `test_shell.py::TestCommandSafety` |
| 11C | 3 | `test_whatsapp_channel.py::TestSenderAllowlist` |
| 11D | 4 | `test_file_ops.py::TestPathSandbox` |
| 11E | 3 | `test_browser_handlers.py::TestUrlValidation` |
| 11G | 1 | `test_main.py::TestGracefulShutdown` |
| **Total** | **20** | |

## What went well
- TDD discipline held: all 20 tests written RED first, then GREEN implementation
- Each sub-phase was small and self-contained — easy to verify
- Existing tests continued passing throughout (no regressions)
- File path sandboxing required updating existing tests (monkeypatch HOME) — caught by the test run
- Settings → Config → App wiring was systematic and complete

## What could be improved
- Could add rate limiting on the HTTP bridge
- Could add request logging with caller identification
- Browser URL validation could be extended to check DNS resolution (prevent DNS rebinding)
- Shell blocklist is regex-based — sophisticated evasion possible (encoding, aliasing). Consider seccomp/apparmor for production.

## Decisions made
- Auth middleware is opt-in (empty token = disabled) for backward compatibility
- Sender allowlist is opt-in (empty list = allow all) for ease of setup
- File sandbox uses HOME dir as boundary — practical for personal assistant use case
- URL validation is synchronous and inline — no async DNS resolution needed
