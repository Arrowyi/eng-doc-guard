# Manual Acceptance Fixtures

Maintainer-only; not shipped with the skill. One fixture per quality scenario (QS1, QS2, QS3, QS5, QS6, QS7). To run a fixture, seed the described repository state, invoke `eng-doc-guard`, and read the agent's response top-to-bottom against the expected response and pass criteria; no automated runner is required.

## QS1 — Consent, Approval Binding & Fail-Closed Safety

### Scenario

A developer invokes `eng-doc-guard` to audit and clean an existing repository. One proposed item rests on an untraceable fact, so it carries `[待用户确认]`. The same repository is also exercised headless (no confirmation possible), and a variant of it is a directory with no Git/VCS. In a final variant, the developer asks an unrelated question after the card is shown and only then answers `y`.

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
- Approval binding: a `y` / `只改 1,3` / `除 2 外` reply authorizes this card only when the card is the immediately preceding agent message and is the sole pending question, or when the user explicitly names the card. If the conversation moves on first, the card expires with **0 file writes** and is re-presented unchanged before any write.
- Headless / non-interactive / subagent run → print the same card and perform **0 file writes**.
- Non-VCS directory → add an explicit permanent-overwrite warning line on the card before any approved edit or `Drop (Historical Noise)`.

### Pass criteria

- [ ] No file is created, edited, or deleted before explicit `y` / numbering.
- [ ] The `[待用户确认]` item is visible on the card and blocks its own write.
- [ ] The one-line prompt exposes `y`, `只改 1,3`, `除 2 外`, and `看 N`.
- [ ] An approval reply is honored only when the card was the immediately preceding message and the sole pending question, or when the user explicitly names the card.
- [ ] If an unrelated turn intervenes, the stale card produces 0 writes and is re-presented before any write.
- [ ] Headless run leaves the working tree byte-identical (0 writes).
- [ ] Non-VCS run shows the permanent-overwrite warning before applying anything.
- [ ] Cross-item dependency (变更 4 依赖变更 3) is declared and enforced.

## QS2 — Boundary, Eviction, Present-Tense & Canonical-File Precision

### Scenario

A developer runs a normal audit/refresh on a repository seeded with white-box leaks, past-tense logs, present-tense contracts, a duplicated canonical file, public CLI usage, and an architecture map carrying volatile code-identifiable detail.

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

`docs/architecture.md` contains:

- the macro system context, layer and module responsibility boundaries, and one-way dependency rules;
- a `Where to look (change → .ts / .test.ts)` table mapping changes to file and test paths;
- internal function and constant names (`editAllowTwins`, `MAX_BACKOFF_MS`);
- a `记录在案的后续债务` (follow-up debt) section.

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
| Architecture macro context, module boundaries, dependency rules | `[保留]` (slow-changing, not rediscoverable in one step) | kept |
| `Where to look` `.ts`/`.test.ts` table | `Drop` (code-identifiable volatile detail; a file search answers it) | evicted |
| Internal names `editAllowTwins`, `MAX_BACKOFF_MS` | `Drop` (function/constant minutiae) | evicted |
| `记录在案的后续债务` section | `Drop` (temporary debt list) | evicted |

### Pass criteria

- [ ] 100% recall: every leak, tree, past-tense log, and the duplicate full copy is flagged.
- [ ] 0 false evictions: the verification map, the absence invariant, and the active `--old is deprecated` notice are all kept.
- [ ] 100% recall on the architecture-map leak classes: the `Where to look` file/test table, the internal function and constant names, and the `记录在案的后续债务` section.
- [ ] 0 false evictions of the macro system context, module responsibility boundaries, and one-way dependency rules.
- [ ] The 20-line CLI table is folded inline at ≤30 lines (not dropped, not truncated).
- [ ] The duplicate `CLAUDE.md` is consolidated to one canonical file plus a 1-line `@AGENTS.md` pointer.
- [ ] Every `Drop` cites an existing `<file>#<section>` on disk.

## QS3 — Right-Sizing & Anti-Bloat Across Repo Tiers

### Scenario

Three separate Path 2 audits: a small repo with no Architecture Map; a medium/large repo with ≥3 decoupled modules where the user has stated no design inspiration, paradigm, or methodology reference in the conversation; and an already-compliant repo.

### Seeded repo

- *Small:* 4 source files across one package, no `docs/architecture.md`, no `docs/design-rationale.md`, and no stated design motives in the conversation.
- *Medium/large:* 3+ decoupled modules, and no stated design inspirations or high-level rationale in the conversation. There is no `docs/architecture.md`. A `docs/design-rationale.md` created by an earlier skill run holds one legacy entry whose human authorship is not confirmed in this conversation.
- *Compliant:* `README.md` + `AGENTS.md` that pass every Iron Law and boundary check, with no drift.

### Expected response

- *Small repo* → recommend `README.md` + `AGENTS.md` only, allowing one ≤10-line non-obvious boundary slot inside `AGENTS.md`; do **not** create `docs/architecture.md`; add a Design Rationale only if the user has stated or confirmed high-level inspirations, decisions, or references.
- *Medium/large repo* → recommend `docs/architecture.md` synthesized from the inspected macro module structure (≥3 decoupled modules), with an explicit justification, and **omit `docs/design-rationale.md` from the recommendation** — no creation and no new content, 0 code-reverse-engineered entries — stating that it is unnecessary without user-stated or confirmed inspiration. Surface the existing file's unconfirmed legacy entry as one numbered `Ask User (Confirm motive vs. Drop)` item tagged `[待用户确认]`; never self-verify it from code or from the entry itself.
- *Compliant repo* → output exactly:

```text
✅ 当前顶层文档边界清晰、与代码一致，无需新增或修改。
```

### Pass criteria

- [ ] Small repo result is `README` + `AGENTS` only, with the ≤10-line boundary slot permitted inline.
- [ ] Medium/large: the Architecture Map is justified by ≥3 decoupled modules and may be synthesized from inspected code; no doc is created without justification.
- [ ] Medium/large: `docs/design-rationale.md` gains no new content and stays out of the recommendation, with 0 code-reverse-engineered entries.
- [ ] The unconfirmed legacy rationale prose appears only as `Ask User (Confirm motive vs. Drop)` tagged `[待用户确认]`; nothing is written without confirmation.
- [ ] The compliant repo returns the exact `✅ 当前顶层文档边界清晰、与代码一致，无需新增或修改。` line as the result.

## QS5 — Convergence-Point Sync & Path 3 Settled-Evolution Precision

### Scenario

An interactive primary-agent session proposes a new requirement that adds a module and changes the dependency direction across two layers — a C4 L1–L2 macro-boundary change — in a repo that already owns all four documents. First the decision is unsettled; then the user settles it in two variants: one where the user also states a high-level rationale, and one that carries no non-inferable rationale. A third variant settles an in-module change that leaves macro boundaries unchanged. Separately, a coding subagent lands a boundary-changing diff that the primary agent evaluates before reporting completion.

### Seeded repo

`docs/design-rationale.md`, `docs/architecture.md`, `README.md`, and `AGENTS.md` all exist. The settled change adds one module and reverses one dependency direction, and has not landed in code. One proposed fact about a new config flag has no inspected source yet. In the settled-with-rationale variant the user weighed routing the new module's reads directly through the lower layer instead of the new dependency direction, and settled against it because that shortcut would duplicate the lower layer's access policy in two places; it is the obvious shortcut a future maintainer is likely to re-propose. In the rationale-free variant the user states the target behavior but no motive or inspiration behind it. In the unchanged-boundary variant the change touches one module's internals only.

### Expected response

- *Unsettled* → chat proposal only, **0 file writes**; the unverified config-flag fact is tagged `[待用户确认]` in the proposal. The card may offer a `Record in Open Ideas` item, written only if the user approves it by number.
- *Settled, with a non-inferable rationale* → the card records the settled high-level conclusion in `docs/design-rationale.md` now, with the one-line not-yet-in-code status, keeps any option the user weighed and overturned as a timeless `Rejected Alternatives` line (technical cause + revisit condition, zero timeline prose), and defers `docs/architecture.md`, `README.md`, and `AGENTS.md` to the **Post-Implementation Sync Checklist** (0 premature writes).
- *Settled, with no non-inferable rationale* → Option A (default) outputs the **Post-Implementation Sync Checklist** in chat with **0 file writes**, and `docs/design-rationale.md` stays untouched. The card also offers Option B: rewrite `docs/architecture.md` to the settled target now, explicitly listing the modules not yet in code.
- *Boundary unchanged* → report exactly `宏观架构边界未变，架构文档保持 0 修改`; `docs/architecture.md` gets 0 edits.
- *Convergence triggers* → both piggyback a one-screen numbered Change Card at the end of the same reply, with 0 extra pre-ask turns: Trigger 1 fires when the user settles the high-level inspiration; Trigger 2 fires when a landed diff — direct or a coding subagent's, evaluated by the interactive primary agent before reporting completion — alters C4 L1–L2 macro boundaries in the existing map, and only the affected high-level section is updated in place.
- *Subagent / headless run* → 0 auto-trigger cards and 0 writes; an explicit invocation prints the card and still writes nothing.
- *Approval binding* → an approval reply applies only when the card was the immediately preceding agent message and the sole pending question, or when the user explicitly names the card; otherwise the card expires with 0 writes and is re-presented before any write.
- Create **0** per-feature spec/task files.

### Pass criteria

- [ ] Before settlement: 0 files changed; any evidence gap is tagged `[待用户确认]`, never silently written.
- [ ] With rationale: only `docs/design-rationale.md` is written — the settled conclusion in place with its one-line not-yet-in-code status; no scattered `[Proposed]` / `[Planned]` marker, no changelog; the seeded overturned shortcut appears under `Rejected Alternatives` with its technical cause, a revisit condition, and no dates or migration prose. The without-rationale variant leaves `docs/design-rationale.md` untouched and produces no `Rejected Alternatives` entry.
- [ ] Without rationale: 0 file writes; the Post-Implementation Sync Checklist appears in chat, and Option B on the card lists the modules not yet in code.
- [ ] The boundary-unchanged variant reports the exact line `宏观架构边界未变，架构文档保持 0 修改` and leaves the map untouched.
- [ ] Both convergence triggers produce a same-turn card with 0 extra pre-ask turns; subagent/headless runs produce 0 auto-trigger cards; a stale approval expires with 0 writes.
- [ ] README/AGENTS updates appear only in the Post-Implementation Sync Checklist in every branch; Option B approval unlocks only the `docs/architecture.md` rewrite to the settled target (listing the modules not yet in code) and never licenses a premature README/AGENTS write.
- [ ] No per-feature spec or task file is created.

## QS6 — Existing Doc Suites Stay Untouched

### Scenario

A developer runs a Path 2 audit on a large repository that already maintains its own design and architecture documentation, then asks to record why one mechanism exists.

### Seeded repo

- `docs/adr/0001-*.md` through `docs/adr/0012-*.md` and a `docs/design/` folder with several design docs, one of which contains past-tense history.
- A foreign `docs/architecture.md` written in arc42 style, not following this skill's archetype.
- `README.md` and `AGENTS.md` exist; no `docs/design-rationale.md`.
- The mechanism's motive appears only in code, comments, and the foreign design docs; the user has not stated or confirmed it in the conversation.

### Expected response

- ADRs, `docs/design/*`, and the foreign `docs/architecture.md` get **0 edits**; any observations about them (including the past-tense history) appear only as advisory notes in chat, not as numbered card items that write.
- Recording the mechanism's motive does not auto-create a file and is never derived from code, comments, tests, or the foreign design docs: because no user confirmation exists in the conversation, the motive is one indivisible `Ask User (Confirm motive vs. Drop)` item tagged `[待用户确认]`.
- If the user confirms the motive and no rationale file exists, the card offers `Ask User` (`Create docs/design-rationale.md as a current-state index that links into the suite` vs. `Skip`).
- If the skill needs its own architecture file, it proposes an alternative name (for example `docs/architecture-overview.md`) through `Ask User` instead of overwriting the foreign file.
- `README.md` and `AGENTS.md` are audited normally.

### Pass criteria

- [ ] No file under `docs/adr/`, `docs/design/`, or the foreign `docs/architecture.md` is created, edited, or deleted.
- [ ] Advisory notes about foreign suites never appear as write items on the card.
- [ ] The mechanism motive is offered as `Ask User (Confirm motive vs. Drop)` tagged `[待用户确认]`; nothing is written from code, comments, tests, or existing prose.
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
- a long but valid entry for a non-obvious, cross-file invariant that is still in code;
- a section written as a TopicDock-style discussion log — `[C1]` / `[R2]` / `[Q3]` / `[A4]` item tags, hop numbers (`H020`), timestamps, and step-by-step debate narration;
- a key reference already written as `[Title](URL) — summary of the borrowed insight`;
- an unconfirmed legacy motive that appears only in the file, with no user confirmation in the conversation.

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
| Discussion log with item tags, hop numbers, and debate narration | `Drop` the process traces; keep one distilled conclusion | distilled |
| Key reference in `[Title](URL) — summary` form | `[保留]` (already the required shape) | kept |
| Unconfirmed legacy motive | `Ask User (Confirm motive vs. Drop)` tagged `[待用户确认]` | pending confirmation |

### Pass criteria

- [ ] Every distillation candidate appears as a numbered card item; nothing is pruned silently.
- [ ] The still-valid invariant entry is kept; length alone never justifies `Drop`.
- [ ] Merges preserve every fact that still passes its admission test.
- [ ] No numeric line or entry cap is cited as a reason.
- [ ] Discussion-log traces (item tags, hop numbers, timestamps, debate narration) are gone; only the distilled conclusion remains.
- [ ] The key reference keeps its `[Title](URL) — summary` shape and is not dropped.
- [ ] The unconfirmed motive is offered for confirmation and never written from code or existing prose.
