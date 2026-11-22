# Examples & Manual Audit Checklist

On-demand companion to `SKILL.md`. **Part A** gives worked before/after evictions. **Part B** gives one manual acceptance fixture per quality scenario (QS1, QS2, QS3, QS5). To run a fixture, seed the described repository state, invoke `eng-doc-guard`, and compare the response against the expected table and pass criteria — no automated runner is required.

Across every example, `Drop` must cite a section already on disk, `Fold` respects the ≤30-line / ≤10-line caps, and no write happens before the Change Card is confirmed.

---

## Part A — Worked Before / After Evictions

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

---

## Part B — Manual Acceptance Fixtures

Each fixture uses the four blocks below. Run the seeded repo, then read the agent's response top-to-bottom.

## QS1 — Consent & Fail-Closed Safety

### Scenario

A developer invokes `eng-doc-guard` to audit and clean an existing repository. One proposed item rests on an untraceable fact, so it carries `[待用户确认]`. The same repository is also exercised headless (no confirmation possible), and a variant of it is a directory with no Git/VCS.

### Seeded repo

- `README.md` with one internal SQL leak (`LIMIT 3`) and a 20-line CLI table.
- `AGENTS.md` with a directory tree and a `Change → Verification` section. The seeded `Change → Verification` row for one module has **no** runnable command anywhere in the repo (an evidence gap).
- No `.git/` directory in the non-VCS variant.

### Expected response

Interactive run — present this card and stop before any write:

```text
[保留] README.md 的安装与快速开始；AGENTS.md 的已有 Change → Verification 行。
[变更 1 · 删除 | 铁律 #1：README 内部 SQL 子句 LIMIT 3]
[变更 2 · 折叠 | 铁律 #2：README 20 行 CLI 表折入 ≤30 行使用段]
[变更 3 · 待补 | [待用户确认] 缺少可追溯的验证命令，暂不写入 Change → Verification]
[变更 4 · 依赖变更 3 | 铁律 #2：为同上模块补齐验证行，须待变更 3 确认后生效]
回复 y 全部应用 / 只改 1,3 按编号挑选 / 除 2 外 排除某项 / 看 N 展开第 N 项全文
```

- Item 3 stays `[待用户确认]` and is **excluded from file writes** until the user supplies or confirms the command.
- Item 4 depends on item 3: approving item 3 while excluding item 4 (or vice versa) drops the dependent item too.
- Headless / non-interactive / subagent run → print the same card and perform **0 file writes**.
- Non-VCS directory → add an explicit permanent-overwrite warning line on the card before any approved edit or `Drop (Historical Noise)`.

### Pass criteria

- [ ] No file is created, edited, or deleted before explicit `y` / numbering.
- [ ] The `[待用户确认]` item is visible on the card and blocks its own write.
- [ ] The one-line prompt exposes `y`, `只改 1,3`, `除 2 外`, and `看 N`.
- [ ] Headless run leaves the working tree byte-identical (0 writes).
- [ ] Non-VCS run shows the permanent-overwrite warning before applying anything.
- [ ] Cross-item dependency (变更 4 依赖变更 3) is declared and enforced.

## QS2 — Boundary, Eviction, Present-Tense & Canonical-File Precision

### Scenario

A developer runs a normal audit/refresh on a repository seeded with white-box leaks, past-tense logs, present-tense contracts, a duplicated canonical file, and public CLI usage.

### Seeded repo

`README.md` contains:

- the private identifier `live_refs == 0` and the SQL clause `LIMIT 3`;
- a past-tense version log (for example, "v1.2 (2024-03): refactored the store layer");
- the present-tense line `--old is deprecated, use --new`;
- a 20-line public CLI flag table.

`AGENTS.md` contains:

- a directory tree;
- a past-tense changelog paragraph;
- the present-tense absence invariant "Do not use external runtime imports in `dist/`";
- a `Change → Verification` map.

A duplicate full `CLAUDE.md` (same body as `AGENTS.md`) also exists.

### Expected response

A numbered Change Card whose per-item dispositions are:

| Seeded item | Disposition | Kept? |
|---|---|---|
| `live_refs == 0` | `Drop` (Iron Law #1) | evicted |
| `LIMIT 3` | `Drop` (Iron Law #1) | evicted |
| Past-tense version log | `Drop` (Iron Law #3, historical noise) | evicted |
| `--old is deprecated, use --new` | `[保留]` (present-tense, Iron Law #1 passes) | kept |
| 20-line public CLI flag table | `Fold` inline (≤30 lines, no reference file) | kept, folded |
| `AGENTS.md` directory tree | `Drop` (Iron Law #2 static fact) | evicted |
| `AGENTS.md` past-tense changelog | `Drop` (Iron Law #3) | evicted |
| Absence invariant "Do not use external runtime imports in `dist/`" | `[保留]` (Iron Law #2) | kept |
| `Change → Verification` map | `[保留]` (Iron Law #2) | kept |
| Duplicate full `CLAUDE.md` | `Drop` duplicate + add 1-line `@AGENTS.md` pointer (one numbered item) | consolidated |

### Pass criteria

- [ ] 100% recall: every leak, tree, past-tense log, and the duplicate full copy is flagged.
- [ ] 0 false evictions: the verification map, the absence invariant, and the active `--old is deprecated` notice are all kept.
- [ ] The 20-line CLI table is folded inline at ≤30 lines (not dropped, not truncated).
- [ ] The duplicate `CLAUDE.md` is consolidated to one canonical file plus a 1-line `@AGENTS.md` pointer.
- [ ] Every `Drop` cites an existing `<file>#<section>` on disk.

## QS3 — Right-Sizing & Anti-Bloat Across Repo Tiers

### Scenario

Three separate Path 2 audits: a small repo with no `ARCHITECTURE.md`; a medium/large repo with ≥3 decoupled modules and non-trivial trade-offs; and an already-compliant repo.

### Seeded repo

- *Small:* 4 source files across one package, no `ARCHITECTURE.md`, no `docs/design*.md`.
- *Medium/large:* 3+ decoupled modules with a real architectural trade-off, still no `ARCHITECTURE.md` or `docs/design*.md`.
- *Compliant:* `README.md` + `AGENTS.md` that pass every Iron Law and boundary check, with no drift.

### Expected response

- *Small repo* → recommend `README.md` + `AGENTS.md` only, allowing one ≤10-line non-obvious boundary slot inside `AGENTS.md`; do **not** create `ARCHITECTURE.md`.
- *Medium/large repo* → recommend `ARCHITECTURE.md` (≥3 decoupled modules) and/or a `Technical Design Doc` (non-trivial trade-offs), each with an explicit justification, and state why any omitted doc is unnecessary; never force all four.
- *Compliant repo* → output exactly:

```text
✅ 当前顶层文档边界清晰、与代码一致，无需新增或修改。
```

### Pass criteria

- [ ] Small repo result is `README` + `AGENTS` only, with the ≤10-line boundary slot permitted inline.
- [ ] Medium/large additions are justified by ≥3 modules or real trade-offs; no doc is created without justification.
- [ ] No `ARCHITECTURE.md` or `Technical Design Doc` is created for a repo that does not need one.
- [ ] The compliant repo returns the exact `✅ 当前顶层文档边界清晰、与代码一致，无需新增或修改。` line as the result.

## QS5 — Path 3 Settled-Evolution Precision

### Scenario

A developer proposes a new requirement that stays within existing module boundaries. First the decision is unsettled; then the user explicitly confirms it.

### Seeded repo

`docs/design.md` (a `Technical Design Doc`), `ARCHITECTURE.md`, `README.md`, and `AGENTS.md` all exist. The proposed change touches one module's internals and does not move C4 L1–L2 macro boundaries. One proposed fact about a new config flag has no inspected source yet.

### Expected response

- *Unsettled* → chat proposal only, **0 file writes**; the unverified config-flag fact is tagged `[待用户确认]` in the proposal.
- *User-confirmed* →
  - Rewrite the affected `docs/design.md` section in place to the current settled state.
  - Move the overturned approach into a timeless `Rejected Alternatives` entry (technical cause + revisit condition, zero timeline prose).
  - When macro boundaries are unchanged, report exactly: `宏观架构边界未变，ARCHITECTURE.md 保持 0 修改`.
  - Defer `README.md` / `AGENTS.md` ripple items to a **Post-Implementation Sync Checklist** (no premature writes).
  - Create **0** per-feature spec/task files.

### Pass criteria

- [ ] Before confirmation: 0 files changed; any evidence gap is tagged `[待用户确认]`, never silently written.
- [ ] After confirmation: `docs/design.md` is rewritten in place (no `[Proposed]` / `[Planned]` marker, no changelog).
- [ ] The overturned approach appears under `Rejected Alternatives` with no dates or migration prose.
- [ ] The exact line `宏观架构边界未变，ARCHITECTURE.md 保持 0 修改` is reported when boundaries are unchanged, and `ARCHITECTURE.md` gets 0 edits.
- [ ] README/AGENTS updates appear only in the Post-Implementation Sync Checklist.
- [ ] No per-feature spec or task file is created.
