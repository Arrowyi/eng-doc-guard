# Worked Examples

On-demand companion to `SKILL.md`: worked before/after rewrites showing how the rules apply.

Across every example, `Drop` must cite a section already on disk (or the code site proving a mechanism is gone), `Fold` respects the ≤30-line / ≤10-line caps, `Merge` preserves every fact that still passes its admission test, and no write happens before the Change Card is confirmed.

### A1. `README.md` — white-box mechanics evicted to 0 lines

**Seed (to evict).**

```text
## How storage works
Ledger rows are appended with `INSERT ... WHERE live_refs == 0 LIMIT 3`.
SQLite runs in WAL mode; a `.undo-pending.json` sidecar records in-flight rollbacks,
and the self-heal pipeline re-ranks hot rows every 30 seconds.
```

**Result (after):** all of it is removed — 0 lines of replacement. External users never need storage, lock, or ranking mechanics to evaluate, install, or invoke the tool.

**Disposition:** `Drop` for each mechanic; reason = Iron Law #1 (Semantic Black-Box Test fails). Observable behavior that passes the test — e.g. "data stays on your machine under `~/.local/share/<app>/`" — is kept instead.

### A2. `AGENTS.md` — directory tree evicted, verification map kept

**Seed (to evict).**

```text
## Layout
src/
  parser/
  store/
  cli/
tests/
```

**Seed (to keep).**

```text
## Change → Verification
| Change | Run |
|---|---|
| src/parser/** | python -m pytest tests/parser |
| src/store/**  | python -m pytest tests/store && python -m mypy src/store |
```

**Result (after):** the directory tree is gone (a file search answers it in one step), while the `Change → Verification` table stays — an agent cannot rediscover that map without multi-step exploration.

**Disposition:** `Drop` the tree (Iron Law #2 static fact); `[保留]` the verification map (First-Try Mistake & Cost Test passes).

### A3. Public CLI table — fold at ≤30 lines, link out at >30

**Case A — 20-line flag table, no usage reference file.** `Fold`: keep the table inline in `README.md`, because it is ≤30 lines and no public usage reference exists.

**Case B — 45-line flag table, or a `docs/cli.md` reference exists.** Do not inline it. Keep 3–5 representative examples and add a link to the full reference. Disposition: `Move to Existing Doc` (target exists) or `Ask User (Drop vs. Create & Move)` (target missing).

**Rule of thumb:** the 30-line cap is a ceiling, not a target — when a reference file already exists, link out even for shorter tables.

### A4. Dual `AGENTS.md` + `CLAUDE.md` full copies → one canonical + 1-line pointer

**Seed (to fix).** `AGENTS.md` and `CLAUDE.md` both contain the same full body.

**Result (after).** Keep `AGENTS.md` as the sole canonical file. Replace the full `CLAUDE.md` body with a 1-line pointer:

```text
@AGENTS.md
```

A Markdown link to `AGENTS.md` is equally valid. Create the pointer only with user consent; in a Claude-only repo, `CLAUDE.md` is the canonical file instead.

**Disposition:** the duplicate body is `Drop` (already present in `AGENTS.md` at proposal time); adding the 1-line pointer is one numbered `[变更]` item, flagged in Path 2 as consolidation.

### A5. Design Rationale: from debate log to distilled entries

**Seed (to rewrite).** `docs/design-rationale.md` contains:

```text
## 2024-05 sync discussion
We first pushed every edit to the server immediately (v0.3), then switched to a
local outbox in v0.5 after users lost edits on flaky networks. Retry backoff came later.
## Outbox format
The outbox is a JSON array written by src/outbox/store.ts with fs.writeFileSync.
```

**Result (after).**

```text
## Local outbox before sync
To keep edits safe on unreliable networks, under the constraint that the app must
work offline, every edit is written to a local outbox first and synced in the
background, accepting that two devices can briefly disagree; revisit if the
product ever requires real-time collaboration.
Rejected alternative: push each edit immediately, not used because a dropped
connection loses the edit.

## Open Ideas
- Show the user how many edits are still waiting to sync.
```

**Disposition:** the timeline prose is rewritten in place as one Y-statement entry (Iron Law #3); the push-immediately option survives only as a timeless `Rejected Alternatives` line because it is likely to be proposed again; the outbox-format paragraph is `Drop` (inferable from `src/outbox/store.ts`); the pending-edits line lands under `Open Ideas` only because the user explicitly asked to record it.

