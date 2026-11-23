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

### A5. Design Rationale — code mechanics and a debate log distilled into inspirations and references

**Seed (to rewrite).** `docs/design-rationale.md` contains:

```text
## Outbox retry backoff
To meet the need for reliable sync, under flaky-network constraints, we use
`computeBackoff(attempt, baseMs=1800000)` in src/outbox/retry.ts.

## 2024-05 sync discussion
[C1] 2024-05-11: first we pushed every edit immediately (v0.3).
[R2] H020: switched to a local outbox after users lost edits on flaky networks.
[Q3] Exponential or linear retry backoff?
[A4] Exponential, settled 2024-05-12.
The outbox is a JSON array written by src/outbox/store.ts with fs.writeFileSync.

## Local-first inspiration
Chosen because the team was inspired by the Ink & Switch local-first essay:
an edit must survive a dropped connection and sync later.

## Lock file
A separate lock file exists because it was easier at the time.
```

**Result (after).**

```text
## Local-first architecture
The product is built local-first: every edit is written to a local outbox first and
synced in the background, so an edit survives a dropped connection. Two devices may
briefly disagree; the accepted cost is eventual consistency and manual conflict
resolution. Revisit if the product ever requires real-time collaborative editing.
Rejected alternative: push each edit immediately — not used because a dropped
connection loses the edit.

## Key references
- [Local-first software](https://www.inkandswitch.com/local-first/) — framed the offline-first, background-sync model and its eventual-consistency trade-off.

## Open Ideas
- Show the user how many edits are still waiting to sync.
```

**Disposition:** the outbox-format paragraph and the `computeBackoff(...)` retry entry are `Drop` (code-identifiable mechanics inferable from `src/outbox/store.ts` and `src/outbox/retry.ts`); the backoff reason moves to a 1–3 line code comment at that site. The `[C1]`/`[R2]`/`[Q3]`/`[A4]` debate log with hop and timestamp tags is stripped into one conclusion-only paragraph (Iron Law #3). The local-first inspiration and its reference were stated by the user in the conversation, so they are distilled in place with the settled decision, the accepted trade-off, and the revisit condition; the push-each-edit-immediately option was weighed and overturned by the user in that same conversation, so it survives only as the timeless `Rejected Alternatives` line with its technical cause. The lock-file motive has no user confirmation in the conversation, so it is `Ask User (Confirm motive vs. Drop)`, tagged `[待用户确认]` — never self-verified from code or repo prose, written only if the user confirms. The pending-edits line lands under `Open Ideas` only because the user explicitly asked to record it.

### A6. Architecture Map — volatile file lookups and debt evicted, macro boundaries kept

**Seed (to rewrite).** `docs/architecture.md` contains:

```text
## System context
The CLI reads local files, applies edits, and syncs them through a background queue;
the sync layer reaches the remote store over HTTPS and lies behind the CLI.

## Layer responsibilities
- `cli/` — argument parsing and user-facing output; it does not own persistence.
- `sync/` — outbox, retry, and conflict detection; it does not render output.
- `store/` — durable persistence; it does not decide when to sync.

## Dependency rules
`cli → sync → store`, plus `sync → remote API`. No reverse imports: `store/` never
imports `sync/`, and `sync/` never imports `cli/`.

## Invariants & fault boundaries
Every edit is persisted to the outbox before any network call; a failed sync leaves
the outbox intact, so a remote failure never loses a local edit.

## Where to look
| Change / problem | Files |
|---|---|
| retry backoff | src/sync/retry.ts, test/sync/retry.test.ts |
| auth token refresh | src/auth/token.ts, test/auth/token.test.ts |

## Sync internals
`MAX_BACKOFF_MS = 1800000`; `editAllowTwins()` deduplicates queue entries.

## Follow-up Debt
- Split src/sync/queue.ts once it passes 800 lines.
- Rename `legacyFlush()` after the next release.
```

**Result (after).**

```text
## System context
The CLI reads local files, applies edits, and syncs them through a background queue;
the sync layer reaches the remote store over HTTPS and lies behind the CLI.

## Layer responsibilities
- `cli/` — argument parsing and user-facing output; it does not own persistence.
- `sync/` — outbox, retry, and conflict detection; it does not render output.
- `store/` — durable persistence; it does not decide when to sync.

## Dependency rules
`cli → sync → store`, plus `sync → remote API`. No reverse imports: `store/` never
imports `sync/`, and `sync/` never imports `cli/`.

## Invariants & fault boundaries
Every edit is persisted to the outbox before any network call; a failed sync leaves
the outbox intact, so a remote failure never loses a local edit.
```

**Disposition:** the `Where to look` file/test table, the internal constants and helper name (`MAX_BACKOFF_MS`, `editAllowTwins`), and the `Follow-up Debt` list are all `Drop` — a file search answers the table in one step, the names and numbers are code-identifiable, and the debt list is temporary (the map's volatile-detail eviction). The macro module roles, one-way dependency rules, and the persist-before-sync invariant are `[保留]`: they are slow-changing and not rediscoverable in one step. Each negative boundary claim ("does not own persistence") was checked against the module's imports; any claim that could not be verified that way would carry `[待用户确认]` and stay out of the write until confirmed.

