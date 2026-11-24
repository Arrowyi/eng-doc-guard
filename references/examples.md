# Worked Examples

On-demand companion to `SKILL.md`: worked before/after rewrites showing how the rules apply.

Across every example, `Drop` must cite a section already on disk (`<file>#<section>`) or the code site proving a mechanism is gone; `Fold` applies the post-eviction relative comparator from `SKILL.md` Section 4, never a numeric cap; `Merge` preserves every fact that still passes its admission test; a surviving project-specific term gets its first-use plain-language gloss on the three human-facing documents; and no write happens before the Change Card is confirmed.

### A1. `README.md` — white-box mechanics evicted to 0 lines

**Seed (to evict).**

```text
## How storage works
Ledger rows are appended with `INSERT ... WHERE live_refs == 0 LIMIT 3`.
SQLite runs in WAL mode; a `.undo-pending.json` sidecar records in-flight rollbacks,
and the self-heal pipeline re-ranks hot rows every 30 seconds.
```

**Result (after):** all of it is removed — 0 lines of replacement. External users never need storage, lock, or ranking mechanics to evaluate, install, or invoke the tool, and these mechanics change across version upgrades behind the public interface.

**Disposition:** `Drop` for each mechanic; reason = Iron Law #1 (Information Hiding / Version-Stability Black-Box Test fails). An observable contract that passes the test — e.g. "data stays on your machine under `~/.local/share/<app>/`" — is kept instead.

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

**Disposition:** `Drop` the tree (Iron Law #2, static fact obtainable from directory layout); `[保留]` the verification map (First-Try Mistake & Cost Test passes).

### A3. Public CLI usage block — fold only under the relative comparator

**Case A — a compact flag table, no usage reference file on disk.** After the Iron Law #1/#3 evictions run, `Fold`: keep the table inline in `README.md`, because no dedicated public CLI/API usage reference file exists on disk **and** the table stays shorter than the surviving core landing-page sections combined (background + capabilities + install/quickstart).

**Case B — an exhaustive flag reference, or a `docs/cli.md` reference already on disk.** Do not inline all of it. When a dedicated usage reference file (`docs/cli.md`, `docs/deployment.md`) already exists on disk, apply the SSOT split: `Drop` from `README.md` the exhaustive usage lines that `docs/cli.md#<section>` already carries and that match the current code (never dropping accurate `README.md` lines in favor of a stale topic doc), and `Move to Existing Doc` as a card-approved, non-enrolling append only for the net-new exhaustive lines not yet in the reference file (appended without writing `<!-- eng-doc-guard:managed -->`), keeping representative usage examples inline and a link to the full reference. `Ask User (Drop vs. Create & Move)` when no reference file exists on disk.

**Rule of thumb:** the comparator is the reader's job, not a line count. When a reference file already exists on disk, link out even for a table that would fit inline; when the usage block would outweigh the surviving core sections, keep representative examples and link out.

### A4. Dual `AGENTS.md` + `CLAUDE.md` full copies → one canonical + 2-line managed pointer

**Seed (to fix).** `AGENTS.md` and `CLAUDE.md` both contain the same full body.

**Result (after).** Keep `AGENTS.md` as the sole canonical file. Replace the full `CLAUDE.md` body with a 2-line managed pointer:

```text
<!-- eng-doc-guard:managed -->
@AGENTS.md
```

Create the pointer only with user consent; the card discloses that line 1 receives the sentinel, so the second file is a thin compatibility pointer rather than a second body. A repo whose strict MDX doc-site parser rejects HTML comments can decline the pointer entirely. In a Claude-only repo, `CLAUDE.md` is the canonical file instead.

**Disposition:** the duplicate body is `Drop` (already present in `AGENTS.md#<section>` at proposal time); adding the pointer is one numbered `[变更]` item (action `纳管` for an existing second file, or `新建` for a fresh pointer), flagged in Path 2 as consolidation. When consolidating an existing unmarked `CLAUDE.md`, item `[变更 N · 纳管]` enrolls `CLAUDE.md` by writing the 2-line managed pointer into it, and the duplicate-body `Drop` declares `[依赖变更 N]` on that enrollment item (or both are packaged into that single indivisible consolidation item); for a fresh pointer file, the action is `新建`.

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
<!-- eng-doc-guard:managed -->
## Local-first architecture
The product is built local-first: every edit goes into a local outbox — a queue of
edits waiting to reach the server — and syncs in the background, so an edit survives
a dropped connection. Two devices may briefly disagree; the accepted cost is eventual
consistency and manual conflict resolution. Revisit if the product ever requires
real-time collaborative editing.
Rejected alternative: push each edit immediately — not used because a dropped
connection loses the edit.

## Key references
- [Local-first software](https://www.inkandswitch.com/local-first/) — framed the offline-first, background-sync model and its eventual-consistency trade-off.

## Open Ideas
- Show the user how many edits are still waiting to sync.
```

**Disposition:** the outbox-format paragraph and the `computeBackoff(...)` retry entry are `Drop` (code-identifiable mechanics inferable from `src/outbox/store.ts` and `src/outbox/retry.ts`); the backoff reason moves to a 1–3 line code comment at that site. The `[C1]`/`[R2]`/`[Q3]`/`[A4]` debate log with hop and timestamp tags is stripped into one conclusion-only paragraph (Iron Law #3). The surviving term "outbox" gets a first-use plain-language gloss via `Rewrite in Place` (`改写/补释`) — the code identifier `src/outbox/` stays verbatim while the prose explains it once. The local-first inspiration and its reference were stated by the user in the conversation, so they are distilled in place with the settled decision, the accepted trade-off, and the revisit condition; the push-each-edit-immediately option was weighed and overturned by the user in that same conversation, so it survives only as the timeless `Rejected Alternatives` line with its technical cause. The lock-file motive has no user confirmation in the conversation, so it is `Ask User (Confirm motive vs. Drop)`, tagged `[待用户确认]` — never self-verified from code or repo prose, written only if the user confirms. The pending-edits line lands under `Open Ideas` only because the user explicitly asked to record it.

### A6. Architecture Map — volatile detail evicted, macro boundaries and a core flow kept

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
<!-- eng-doc-guard:managed -->
## System context
The CLI reads local files, applies edits, and syncs them through a background queue;
the sync layer reaches the remote store over HTTPS and lies behind the CLI.

## Layer responsibilities
- `cli/` — argument parsing and user-facing output; it does not own persistence.
- `sync/` — outbox, retry, and conflict detection; it does not render output.
- `store/` — durable persistence; it does not decide when to sync.

## Core business flow: edit → sync
1. Trigger: the user edits a file through `cli/`.
2. `cli/` validates the edit and hands it to `sync/`, which records it in the outbox
   and returns control; `store/` is not on this path.
3. In the background, `sync/` drains the outbox to the remote store; the edit's
   durable owner moves from `sync/`'s outbox to the remote store only after the
   remote store acknowledges it.
4. Guaranteed invariant: a remote failure leaves the outbox intact, so the edit is
   never lost and is retried on the next drain.

## Dependency rules
`cli → sync → store`, plus `sync → remote API`. No reverse imports: `store/` never
imports `sync/`, and `sync/` never imports `cli/`.

## Invariants & fault boundaries
Every edit is persisted to the outbox before any network call; a failed sync leaves
the outbox intact, so a remote failure never loses a local edit.
```

**Disposition:** the `Where to look` file/test table, the internal constants and helper name (`MAX_BACKOFF_MS`, `editAllowTwins`), and the `Follow-up Debt` list are all `Drop` under **Iron Law #4 (Slow-Changing Macro Altitude / Pace Layering)** — per-file lookup rows and internal function/constant names sit at fast-changing C4 L3–L4 commit velocity and drift on routine commits, and the debt list is temporary. Mechanical file/test lookup rows also fail Iron Law #2, so they are dropped outright rather than moved to `AGENTS.md`; a code-verified cross-file co-change coupling row, by contrast, would be moved as a 1-line rule. A coarse directory tree whose nodes correspond strictly to the macro layers named in the map's prose, with zero individual files, passes Iron Law #4 — or uses `Merge` if it duplicates the layer responsibilities list — whereas a file-level or deep internal tree is `Drop`. The macro module roles, the one-way dependency rules, the new module-interaction-altitude core flow (trigger → participating modules and collaboration order → state-ownership transition and guaranteed invariant, with zero function call stacks), and the persist-before-sync invariant are `[保留]`: they are slow-changing macro structure. The file now opens with `<!-- eng-doc-guard:managed -->` on line 1, so it is managed and Trigger 2 may maintain it. Each negative boundary claim ("does not own persistence") was checked against the module's imports; a claim that could not be verified that way would carry `[待用户确认]` and stay out of the write until confirmed.
