# Development Process

## Phase Lifecycle

Every phase follows four steps in strict order:

### Step 1: PLAN

- Write `docs/phases/phase-N-plan.md` with:
  - Implementation details (file-by-file breakdown)
  - Test plan: what mock tests + what real tests
  - Acceptance criteria (the validation gate)
  - Dependencies / blockers
- Create a new branch off `main`: `phase-N-description`

### Step 2: TEST (write tests first)

- Write unit tests with mocks → all **FAIL** (red)
- Write integration test stubs where applicable
- Commit the failing tests

### Step 3: IMPLEMENT

- Write code to make tests pass
- All tests **GREEN** before moving on
- Run lint (`uv run ruff check src/ tests/`) and type check (`uv run mypy src/jarvis/`)

### Step 4: RETRO

- User shares observations first (prompted by specific questions)
- Claude drafts `docs/phases/phase-N-retro.md` incorporating user's + technical observations
- Retro contents:
  - What worked well
  - Surprises and unexpected findings
  - Deviations from the plan (and why)
  - Implicit assumptions made explicit
  - Scope added or removed for next phase
  - Rationale for key decisions
- Update `CLAUDE.md` with new current state
- Commit + push the branch
- **User merges to `main` and signals to proceed**

---

## Session Workflow

### Start of Session

1. Claude reads `CLAUDE.md` → knows current project state
2. Claude reads `docs/phases/phase-(N-1)-retro.md` → knows what changed last
3. Together we write `docs/phases/phase-N-plan.md` (gory implementation details)
4. Tests first, then implement, then retro

### End of Session

1. Collaborative retro (user observations first → Claude drafts retro doc)
2. Update `CLAUDE.md` current state
3. Commit + push all docs and code to the phase branch

---

## Validation Gates

Every phase has two test tiers that must pass before the phase is complete:

| Tier | Scope | Command | When |
|------|-------|---------|------|
| **Mock** | Unit tests, mocked Letta/APIs | `uv run pytest tests/unit/ -v` | Every phase |
| **Real** | Integration against running Letta | `uv run pytest tests/integration/ -v` | When docker compose is up |
| **Lint** | Code quality | `uv run ruff check src/ tests/` | Every phase |
| **Types** | Type checking | `uv run mypy src/jarvis/` | Every phase |

---

## Git Workflow

```
main ─────●─────────────●─────────────●──────
          │             │             │
          └─ phase-0 ──┘             │
                        └─ phase-1 ──┘
```

- Branch off `main` at the start of each phase
- All work happens on the phase branch
- Commit + push when validation gate passes
- User merges to `main` manually (mindful review)
- User signals to proceed to next phase
- Next phase branches off updated `main`

### Branch Naming

`phase-N-short-description`

Examples:
- `phase-0-infrastructure`
- `phase-1-core-loop`
- `phase-2-first-tools`
- `phase-3-slack`

---

## Retro Format

Each `docs/phases/phase-N-retro.md` follows this structure:

```markdown
# Phase N Retro: <title>

## What Worked
- ...

## Surprises
- ...

## Deviations from Plan
- What changed and why

## Assumptions Made Explicit
- Things we assumed that should be documented

## Scope Changes for Next Phase
- Added: ...
- Removed: ...

## Key Decisions and Rationale
- Decision → Rationale

## Metrics
- Tests: X unit, Y integration (all passing)
- Files changed: N
- Lines of code: ~N
```

---

## Makefile Shortcuts

```makefile
test:        uv run pytest tests/unit/ -v
test-all:    uv run pytest tests/ -v
test-int:    uv run pytest tests/integration/ -v
lint:        uv run ruff check src/ tests/
typecheck:   uv run mypy src/jarvis/
docker-up:   docker compose up -d
run:         uv run python -m jarvis
```
