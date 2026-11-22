# Manual Acceptance Fixtures

Maintainer-only; not shipped with the skill. One fixture per quality scenario (QS1, QS2, QS3, QS5, QS6, QS7). To run a fixture, seed the described repository state, invoke `eng-doc-guard`, and read the agent's response top-to-bottom against the expected response and pass criteria; no automated runner is required.

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

Three separate Path 2 audits: a small repo with no Architecture Map; a medium/large repo with ≥3 decoupled modules and user-stated motives for non-obvious mechanisms; and an already-compliant repo.

### Seeded repo

- *Small:* 4 source files across one package, no `docs/architecture.md`, no `docs/design-rationale.md`, and no stated design motives in the conversation.
- *Medium/large:* 3+ decoupled modules, and the user has explained why one non-obvious mechanism exists; still no `docs/architecture.md` or `docs/design-rationale.md`.
- *Compliant:* `README.md` + `AGENTS.md` that pass every Iron Law and boundary check, with no drift.

### Expected response

- *Small repo* → recommend `README.md` + `AGENTS.md` only, allowing one ≤10-line non-obvious boundary slot inside `AGENTS.md`; do **not** create `docs/architecture.md`.
- *Medium/large repo* → recommend `docs/architecture.md` (≥3 decoupled modules) and/or `docs/design-rationale.md` (user-stated motives), each with an explicit justification, and state why any omitted doc is unnecessary; never force all four.
- *Compliant repo* → output exactly:

```text
✅ 当前顶层文档边界清晰、与代码一致，无需新增或修改。
```

### Pass criteria

- [ ] Small repo result is `README` + `AGENTS` only, with the ≤10-line boundary slot permitted inline.
- [ ] Medium/large additions are justified by ≥3 modules or user-stated motives; no doc is created without justification.
- [ ] No Architecture Map or Design Rationale is created for a repo that does not need one.
- [ ] The compliant repo returns the exact `✅ 当前顶层文档边界清晰、与代码一致，无需新增或修改。` line as the result.

## QS5 — Path 3 Settled-Evolution Precision

### Scenario

A developer proposes a new requirement that stays within existing module boundaries. First the decision is unsettled; then the user explicitly confirms it.

### Seeded repo

`docs/design-rationale.md`, `docs/architecture.md`, `README.md`, and `AGENTS.md` all exist. The proposed change touches one module's internals and does not move C4 L1–L2 macro boundaries. One proposed fact about a new config flag has no inspected source yet. The overturned approach is one a future maintainer is likely to propose again.

### Expected response

- *Unsettled* → chat proposal only, **0 file writes**; the unverified config-flag fact is tagged `[待用户确认]` in the proposal. The card may offer a `Record in Open Ideas` item, written only if the user approves it by number.
- *User-confirmed* →
  - Rewrite the affected `docs/design-rationale.md` entry in place to the settled state, with a one-line not-yet-in-code status while the code has not landed.
  - Keep the overturned approach as a timeless `Rejected Alternatives` line (technical cause + revisit condition, zero timeline prose).
  - When macro boundaries are unchanged, report exactly: `宏观架构边界未变，架构文档保持 0 修改`.
  - Defer `README.md` / `AGENTS.md` ripple items to a **Post-Implementation Sync Checklist** (no premature writes).
  - Create **0** per-feature spec/task files.

### Pass criteria

- [ ] Before confirmation: 0 files changed; any evidence gap is tagged `[待用户确认]`, never silently written.
- [ ] After confirmation: `docs/design-rationale.md` is rewritten in place (no scattered `[Proposed]` / `[Planned]` marker, no changelog); the only pending mark is the entry's not-yet-in-code status line.
- [ ] The overturned approach appears under `Rejected Alternatives` with no dates or migration prose.
- [ ] The exact line `宏观架构边界未变，架构文档保持 0 修改` is reported when boundaries are unchanged, and `docs/architecture.md` gets 0 edits.
- [ ] README/AGENTS updates appear only in the Post-Implementation Sync Checklist.
- [ ] No per-feature spec or task file is created.

## QS6 — Existing Doc Suites Stay Untouched

### Scenario

A developer runs a Path 2 audit on a large repository that already maintains its own design and architecture documentation, then asks to record why one mechanism exists.

### Seeded repo

- `docs/adr/0001-*.md` through `docs/adr/0012-*.md` and a `docs/design/` folder with several design docs, one of which contains past-tense history.
- A foreign `docs/architecture.md` written in arc42 style, not following this skill's archetype.
- `README.md` and `AGENTS.md` exist; no `docs/design-rationale.md`.

### Expected response

- ADRs, `docs/design/*`, and the foreign `docs/architecture.md` get **0 edits**; any observations about them (including the past-tense history) appear only as advisory notes in chat, not as numbered card items that write.
- Recording the mechanism's motive does not auto-create a file: the card offers `Ask User` (`Create docs/design-rationale.md as a current-state index that links into the suite` vs. `Skip`).
- If the skill needs its own architecture file, it proposes an alternative name (for example `docs/architecture-overview.md`) through `Ask User` instead of overwriting the foreign file.
- `README.md` and `AGENTS.md` are audited normally.

### Pass criteria

- [ ] No file under `docs/adr/`, `docs/design/`, or the foreign `docs/architecture.md` is created, edited, or deleted.
- [ ] Advisory notes about foreign suites never appear as write items on the card.
- [ ] No duplicate decision record is created without the user choosing it.
- [ ] Any skill-owned file uses a non-colliding name confirmed by the user.

## QS7 — Distillation Without Over-Pruning

### Scenario

A developer refreshes an existing, skill-owned `docs/design-rationale.md` and `docs/architecture.md` after the codebase has grown and changed.

### Seeded repo

`docs/design-rationale.md` contains:

- an entry for a cache-warming mechanism whose code has been deleted;
- two entries that justify the same original need with slightly different wording;
- an entry explaining a constant that a code comment already explains;
- an `Open Ideas` item that has since landed in code;
- a long but valid entry for a non-obvious, cross-file invariant that is still in code.

`docs/architecture.md` lists twelve small modules one by one, where four coarse groups with one example each would carry the same boundaries.

### Expected response

A Change Card with these distillation items:

| Seeded item | Disposition | Kept? |
|---|---|---|
| Entry for deleted cache-warming code | `Drop` (cites the code site proving removal) | evicted |
| Two same-need entries | `Merge` into one entry | merged |
| Entry duplicating a code comment | `Drop` (inferable from code) | evicted |
| Landed `Open Ideas` item | `Drop`, or promoted into an entry if its motive passes the admission test | evicted or promoted |
| Long valid invariant entry | `[保留]` (still passes its admission test) | kept |
| Twelve-module listing | `Merge` into four groups, each with one example | lifted |

### Pass criteria

- [ ] Every distillation candidate appears as a numbered card item; nothing is pruned silently.
- [ ] The still-valid invariant entry is kept; length alone never justifies `Drop`.
- [ ] Merges preserve every fact that still passes its admission test.
- [ ] No numeric line or entry cap is cited as a reason.
