# Phase 11 Plan: Security Hardening + Public Repo Polish

## Scope

### Security Hardening
- Bearer token auth on all 42 HTTP endpoints (exempt /health, /metrics)
- Shell command safety: blocked pattern filter
- WhatsApp sender allowlist
- File path sandboxing: home directory jail
- Browser URL validation: scheme/host blocking (SSRF prevention)
- Docker compose: remove exposed DB port, request size limits
- Graceful shutdown on SIGTERM

### Public Repo Polish
- README.md with architecture mermaid diagrams
- Demo script (CLI walkthrough)
- .env.example with all env vars documented
- MIT LICENSE

## Sub-phases

1. **11A**: HTTP Bearer Token Auth (CRITICAL)
2. **11B**: Shell Command Safety (CRITICAL)
3. **11C**: WhatsApp Sender Allowlist (HIGH)
4. **11D**: File Path Sandboxing (HIGH)
5. **11E**: Browser URL Validation (MEDIUM)
6. **11F**: Docker Compose + Input Validation (MEDIUM)
7. **11G**: Graceful Shutdown (MEDIUM)
8. **11H**: Demo Script + Repo Polish

## Test target

~20 new tests → ~287 unit + 16 integration = ~303 total
