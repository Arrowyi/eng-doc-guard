# Manual Acceptance Fixtures

Maintainer-only; not shipped with the skill. One fixture per quality scenario (QS1, QS2, QS3, QS5, QS6, QS7). To run a fixture, seed the described repository state, invoke `eng-doc-guard`, and read the agent's response top-to-bottom against the expected response and pass criteria; no automated runner is required. Where a fixture seeds an unmarked pre-existing governed document, the expected response must show the consent-gated enrollment gate: the line-1 `<!-- eng-doc-guard:managed -->` sentinel is written only after the enrollment item is approved, and declining it leaves the file untouched.

## QS1 — Consent, Approval Binding, Fail-Closed Safety & Unmarked-Doc Enrollment Gate

### Scenario

A developer invokes `eng-doc-guard` to audit and clean an existing repository whose `README.md` is an unmarked pre-existing governed document (no first-line sentinel). One proposed item rests on an untraceable fact, so it carries `[待用户确认]`. The same repository is also exercised headless (no confirmation possible), and a variant of it is a directory with no Git/VCS. In a final variant, the developer asks an unrelated question after the card is shown and only then answers `y`.

### Seeded repo

- `README.md`, unmarked (no `<!-- eng-doc-guard:managed -->` first line), with one internal SQL leak (`LIMIT 3`) and a compact 20-line CLI table.
- `AGENTS.md`, already managed (first line `<!-- eng-doc-guard:managed -->`), with a directory tree and a `Change → Verification` section. The seeded `Change → Verification` row for one module has **no** runnable command anywhere in the repo (an evidence gap).
- No `.git/` directory in the non-VCS variant.

### Expected response

Interactive run — present this card and stop before any write; the card opens with the enrollment item for the unmarked `README.md`, and every edit item on that file depends on it:

```text
[保留] AGENTS.md 的已有 Change → Verification 行；README.md 的安装与快速开始。
[变更 1 · 纳管 | 为未纳管的 README.md 首行写入 <!-- eng-doc-guard:managed --> 并纳入本工具维护（拒绝则保持 0 修改）]
[变更 2 · 依赖变更 1 | 铁律 #1：删除 README 内部 SQL 子句 LIMIT 3（须先纳管变更 1）]
[变更 3 · 依赖变更 1 | 折叠：README 的 CLI 表折入使用段——相对比较器：短于 README 现存核心段落，且磁盘上无独立 CLI 参考文件（须先纳管变更 1）]
[变更 4 · 待补 | [待用户确认] 缺少可追溯的验证命令，暂不写入 Change → Verification]
[变更 5 · 依赖变更 4 | 铁律 #2：为同上模块补齐验证行，须待变更 4 确认后生效]
回复 y 全部应用 / 只改 1,3 按编号挑选 / 除 2 外 排除某项 / 看 N 展开第 N 项全文
```

- Item 1 enrolls the unmarked `README.md`; the card discloses that its line 1 becomes `<!-- eng-doc-guard:managed -->`. Items 2 and 3 are edits on that same file, so each declares `[依赖变更 1]`.
- Declining item 1, or excluding it by number, skips items 2 and 3 through transitive dependency exclusion with **0 writes** — the unmarked `README.md` stays byte-identical.
- Item 4 stays `[待用户确认]` and is **excluded from file writes** until the user supplies or confirms the command.
- Item 5 depends on item 4: approving item 4 while excluding item 5 (or vice versa) drops the dependent item too.
- Approval binding: a `y` / `只改 1,3` / `除 2 外` reply authorizes this card only when the card is the immediately preceding agent message and is the sole pending question, or when the user explicitly names the card. If the conversation moves on first, the card expires with **0 file writes** and is re-presented unchanged before any write.
- Headless / non-interactive / subagent run → print the same card and perform **0 file writes**.
- Non-VCS directory → add an explicit permanent-overwrite warning line on the card before any approved edit or `Drop`.

### Pass criteria

- [ ] No file is created, edited, or deleted before explicit `y` / numbering.
- [ ] The card opens with a `纳管` item for the unmarked `README.md`, and that item discloses the line-1 `<!-- eng-doc-guard:managed -->` write.
- [ ] Every edit item on the unmarked file declares `[依赖变更 1]`; declining or excluding item 1 leaves the file byte-identical (0 writes).
- [ ] The `[待用户确认]` item is visible on the card and blocks its own write.
- [ ] The one-line prompt exposes `y`, `只改 1,3`, `除 2 外`, and `看 N`.
- [ ] An approval reply is honored only when the card was the immediately preceding message and the sole pending question, or when the user explicitly names the card.
- [ ] If an unrelated turn intervenes, the stale card produces 0 writes and is re-presented before any write.
- [ ] Headless run leaves the working tree byte-identical (0 writes).
- [ ] Non-VCS run shows the permanent-overwrite warning before applying anything.
- [ ] Cross-item dependency (变更 5 依赖变更 4) is declared and enforced; the enrollment chain (变更 2 / 变更 3 依赖变更 1) is skipped transitively when item 1 is declined.

## QS2 — Four Iron Laws, Seven Dispositions, Human Readability & Canonical-File Precision

### Scenario

A developer runs a normal audit/refresh on a repository seeded with white-box leaks, past-tense logs, present-tense public contracts, a surviving but unexplained public domain term, a duplicated canonical file, public CLI usage, and an architecture map carrying fast-changing C4 L3–L4 implementation detail. The architecture map's `Where to look` table mixes mechanical file/test lookup rows with one row encoding a code-verified cross-file co-change coupling. After the card is shown, the developer challenges the architecture evictions with "architecture.md is for human architects; code-readable content doesn't need to be deleted".

### Seeded repo

`README.md`, `AGENTS.md`, and `docs/architecture.md` are already managed — each carries the first-line `<!-- eng-doc-guard:managed -->` sentinel — so the card's edits to them need no enrollment items. The duplicate full `CLAUDE.md` is unmarked; the consolidation item that rewrites it into the 2-line pointer carries action `纳管`, enrolling it, and the duplicate-body `Drop` declares `[依赖变更 N]` on that enrollment item (per examples A4).

`README.md` contains:

- the private identifier `live_refs == 0` and the SQL clause `LIMIT 3`;
- a past-tense version log (for example, "v1.2 (2024-03): refactored the store layer");
- the present-tense line `--old is deprecated, use --new`;
- an unexplained surviving public domain term on first mention (the project-specific term "outbox", used with no plain-language gloss);
- a compact 20-line public CLI flag table.

`AGENTS.md` contains:

- a directory tree;
- a dead routing pointer to a non-existent `docs/missing-spec.md`;
- a `Change → Verification` map.

A duplicate full `CLAUDE.md` (same body as `AGENTS.md`) also exists.

`docs/architecture.md` contains:

- the macro system context, layer and module responsibility boundaries, one-way dependency rules, and cross-module core business/runtime flows;
- a `Where to look (change → .ts / .test.ts)` table mapping changes to file and test paths, plus one mixed row encoding a cross-file co-change coupling that is verified in inspected code (a variant leaves it unverified in code/config, so it stays unconfirmed in the conversation);
- internal function and constant names (`editAllowTwins`, `MAX_BACKOFF_MS`);
- a `记录在案的后续债务` (follow-up debt) section.

### Expected response

A numbered Change Card whose per-item dispositions are:

| Seeded item | Disposition | Kept? |
|---|---|---|
| `live_refs == 0` | `Drop` (Iron Law #1) | evicted |
| `LIMIT 3` | `Drop` (Iron Law #1) | evicted |
| Past-tense version log | `Drop` (Iron Law #3, historical noise) | evicted |
| `--old is deprecated, use --new` | `[保留]` (public deprecation contract, Iron Law #1 passes) | kept |
| 20-line public CLI flag table | `Fold` inline via the relative comparator (shorter than the surviving core README sections, with no separate CLI reference file on disk) | kept, folded |
| Surviving domain term "outbox" on first mention | `Rewrite in Place` (`改写/补释`) — first-use plain-language gloss, applied after the boundary evictions (evict-before-gloss) | kept, glossed |
| `AGENTS.md` directory tree | `Drop` (Iron Law #2 static fact) | evicted |
| Dead routing pointer to `docs/missing-spec.md` | `Drop` (Iron Law #2; the target path is confirmed absent by directory/file inspection) | evicted |
| `Change → Verification` map | `[保留]` (Iron Law #2) | kept |
| Duplicate full `CLAUDE.md` | `[变更 N · 纳管]` writes the 2-line managed pointer into the existing unmarked file (line 1 `<!-- eng-doc-guard:managed -->`, line 2 `@AGENTS.md`); the duplicate body is a separate `Drop` item (cited against `AGENTS.md#<section>`) that declares `[依赖变更 N]` on that enrollment item | consolidated |
| Architecture macro context, module boundaries, one-way dependencies, core business flows | `[保留]` (Iron Law #4 Pace Layering; slow-changing) | kept |
| `Where to look` `.ts`/`.test.ts` table | `Drop` (Iron Law #4 Pace Layering: C4 L3–L4 mechanical file/test location rows change at routine commit velocity and rot, and also fail Iron Law #2 so they are dropped outright rather than moved to AGENTS.md) | evicted |
| Mixed `Where to look` row encoding a code-verified cross-file co-change coupling | `Move to Existing Doc` into `AGENTS.md` as a 1-line co-change rule (tagged `[待用户确认]` and excluded from writes if unverified in inspected code/config) | moved |
| Internal names `editAllowTwins`, `MAX_BACKOFF_MS` | `Drop` (Iron Law #4 Pace Layering: fast-changing C4 L3–L4 internal function and constant names) | evicted |
| `记录在案的后续债务` section | `Drop` (Iron Law #4; temporary debt list) | evicted |

- The mixed `Where to look` row encoding a code-verified cross-file co-change coupling is routed via `Move to Existing Doc` into `AGENTS.md` as a 1-line co-change rule (per the Universal Evidence Guard it traces to inspected code; if unverified in code/config it is tagged `[待用户确认]` and excluded from writes instead). The mechanical file-lookup table is never imported into `AGENTS.md`.
- Under the developer's challenge ("architecture.md is for human architects; code-readable content doesn't need to be deleted"), the agent re-verifies each item's altitude and explains the two-axis orthogonality — exemption from Iron Law #2 code-inferability is separate from enforcement of Iron Law #4 Pace Layering — keeping `Drop` as the recommended disposition for C4 L3–L4 file/symbol inventories (withdrawing `Drop` only for a qualifying C4 L1–L2 coarse macro tree, which becomes `[保留]` or `Merge`), while honoring any `除 N 外` exclusion with 0 writes.

### Pass criteria

- [ ] 100% recall: every leak, the directory tree, the dead routing pointer, the past-tense log, the duplicate full copy, and the fast-changing architecture detail are flagged.
- [ ] 0 false evictions: the verification map, the `--old is deprecated` notice, and the architecture macro context, module boundaries, one-way dependencies, and core business flows are all kept.
- [ ] Every `Drop` cites the dropped item's location and the violated Iron Law; the dead routing pointer additionally cites the confirmed-absent `docs/missing-spec.md` path (Iron Law #2), and the dropped architecture items cite Iron Law #4.
- [ ] The 20-line CLI table is folded inline via the relative comparator (shorter than the surviving core README sections, with no separate reference file on disk) — not by any numeric cap.
- [ ] The surviving domain term gets a first-use plain-language gloss via `Rewrite in Place` (`改写/补释`), applied after the evictions (evict-before-gloss), and is not dropped.
- [ ] The duplicate `CLAUDE.md` is consolidated to a single canonical file plus the 2-line managed pointer (line 1 `<!-- eng-doc-guard:managed -->`, line 2 `@AGENTS.md`).
- [ ] The duplicate-body `Drop` item on the unmarked `CLAUDE.md` declares `[依赖变更 N]` on the `[变更 N · 纳管]` enrollment item; declining or excluding `N` skips the `Drop` transitively with 0 writes to the unmarked file.
- [ ] The mixed `Where to look` row encoding a code-verified cross-file co-change coupling is routed via `Move to Existing Doc` into `AGENTS.md` as a 1-line co-change rule (or tagged `[待用户确认]` when unverified in inspected code/config), and the mechanical file-lookup table is never imported into `AGENTS.md`.
- [ ] Under the challenge "architecture.md is for human architects; code-readable content doesn't need to be deleted", the agent explains the two-axis orthogonality (exempt from Iron Law #2 code-inferability, governed by Iron Law #4 Pace Layering), keeps `Drop` as the recommendation for C4 L3–L4 file/symbol inventories, and honors `除 N 外` exclusions with 0 writes.
- [ ] The resulting 2-line managed pointer is **not** flagged as a duplicate managed sentinel (thin-pointer exemption); only a second full-body managed document in the same role would be.

## QS3 — Right-Sizing, Anti-Bloat Near-Miss & Unmarked-Compliant Precedence

### Scenario

Four separate Path 2 audits: (a) a small flat repo with one entry point; (b) a near-miss linear 3-module repo whose flow is directly visible from the top-level entry point; (c) a decoupled multi-module repo with an asynchronous cross-module runtime flow and no stated design inspiration, carrying one unconfirmed legacy rationale entry; and (d) an already-compliant repo, in both a managed and an unmarked variant.

### Seeded repo

- *Small flat:* four source files in one package with a single top-level entry point, no `docs/architecture.md`, no `docs/design-rationale.md`, and no stated design motives in the conversation.
- *Near-miss linear:* three modules `cli.py → parser.py → formatter.py` forming a strictly linear call chain directly visible from the top-level entry point, with no `docs/architecture.md`.
- *Decoupled:* modules `cli/`, `sync/`, and `store/` with one-way dependencies and an asynchronous cross-module outbox runtime flow that is not visible from any single entry point. There is no `docs/architecture.md`. A `docs/design-rationale.md` created by an earlier skill run holds one legacy entry whose human authorship is not confirmed in this conversation, and the user states no design inspirations or high-level rationale.
- *Compliant managed:* `README.md` + `AGENTS.md` that pass every Iron Law and boundary check, both carrying the first-line `<!-- eng-doc-guard:managed -->` sentinel.
- *Compliant unmarked:* the same compliant content, but neither file carries the sentinel.

### Expected response

- *Small flat repo* → recommend `README.md` + `AGENTS.md` only, allowing a concise inline note for non-obvious module boundaries inside `AGENTS.md` while no managed Architecture Map exists; once a managed Architecture Map exists (or is created on the same card), that topology moves into the map and `AGENTS.md` keeps only a one-line routing pointer. Do **not** create `docs/architecture.md`; add a Design Rationale only if the user has stated or confirmed high-level inspirations, decisions, or references.
- *Near-miss linear repo* → still recommend `README.md` + `AGENTS.md` only and explicitly decline `docs/architecture.md`, naming the single-entry-point visibility comparison (`cli.py → parser.py → formatter.py` is a linear chain directly visible from the top-level entry point): **0 architecture-doc bloat**.
- *Decoupled repo* → recommend `docs/architecture.md` through an explicit `Ask User` card item that cites the cross-module decoupling and the asynchronous outbox runtime flow, e.g. `[变更 N · 新建 | 结构式右尺寸比较器：多个解耦模块的异步 outbox 运行时流程无法从单一入口点看见；新建受管 docs/architecture.md（首行写入 <!-- eng-doc-guard:managed -->）]`. **Omit `docs/design-rationale.md` from the recommendation** — no creation and no new content, 0 code-reverse-engineered entries — stating that it is unnecessary without user-stated or confirmed inspiration. Surface the existing file's unconfirmed legacy entry as one numbered `Ask User (Confirm motive vs. Drop)` item tagged `[待用户确认]`; never self-verify it from code or from the entry itself.
- *Compliant managed repo* → output exactly:

```text
✅ 当前顶层文档边界清晰、与代码一致，无需新增或修改。
```

- *Compliant unmarked repo* → output that exact line first, then a single optional enrollment card item: `[变更 1 · 纳管 | 可选：为 README.md 与 AGENTS.md 首行添加 <!-- eng-doc-guard:managed --> 标记以开启后续自动收敛维护；不回复或拒绝则保持 0 修改]`, with 0 writes unless approved.

### Pass criteria

- [ ] Small flat repo result is `README` + `AGENTS` only, with no `docs/architecture.md` and no Design Rationale without user-stated or confirmed inspiration.
- [ ] Near-miss linear repo result is `README` + `AGENTS` only, with the `docs/architecture.md` decline justified by the single-entry-point visibility comparison and **0 architecture-doc bloat**.
- [ ] Decoupled repo recommends the Architecture Map through an explicit `Ask User` item that cites the cross-module decoupling and the asynchronous runtime flow, and that item discloses the line-1 `<!-- eng-doc-guard:managed -->` write.
- [ ] Decoupled repo: `docs/design-rationale.md` gains no new content and stays out of the recommendation, with 0 code-reverse-engineered entries.
- [ ] The unconfirmed legacy rationale prose appears only as `Ask User (Confirm motive vs. Drop)` tagged `[待用户确认]`; nothing is written without confirmation.
- [ ] The compliant managed repo returns the exact `✅ 当前顶层文档边界清晰、与代码一致，无需新增或修改。` line alone.
- [ ] The compliant unmarked repo returns that exact line first, then exactly one optional enrollment item that discloses the line-1 sentinel write and keeps 0 writes if declined or ignored.
- [ ] No fixed numeric cap is cited to justify any include or omit decision.

## QS5 — Convergence-Point Sync, Core Business Flow Updates & Unmarked-Map Silence

### Scenario

An interactive primary-agent session proposes a new requirement that adds a module and changes the dependency direction across two layers — a C4 L1–L2 macro-boundary change — in one repo whose Architecture Map is managed and, in a second variant, whose only `docs/architecture.md` is unmarked. First the decision is unsettled; then the user settles it in two variants: one where the user also states a high-level rationale, and one that carries no non-inferable rationale. A further variant settles an in-module change that leaves macro boundaries unchanged. Separately, a coding subagent lands a diff that changes a cross-module core business/runtime flow, and the interactive primary agent evaluates it before reporting completion.

### Seeded repo

In the managed variant, `docs/design-rationale.md`, `docs/architecture.md`, `README.md`, and `AGENTS.md` all exist and their governed files carry the first-line `<!-- eng-doc-guard:managed -->` sentinel. In the unmarked variant the same files exist but `docs/architecture.md` lacks the sentinel. The settled change adds one module and reverses one dependency direction, and has not landed in code. One proposed fact about a new config flag has no inspected source yet. In the settled-with-rationale variant the user weighed routing the new module's reads directly through the lower layer instead of the new dependency direction, and settled against it because that shortcut would duplicate the lower layer's access policy in two places; it is the obvious shortcut a future maintainer is likely to re-propose. In the rationale-free variant the user states the target behavior but no motive or inspiration behind it. In the unchanged-boundary variant the change touches one module's internals only. In the landed variant a coding subagent's diff reroutes the edit → persist path so it crosses `sync/` before reaching `store/`.

### Expected response

- *Unsettled* → chat proposal only, **0 file writes**; the unverified config-flag fact is tagged `[待用户确认]` in the proposal. The card may offer a `Record in Open Ideas` item, written only if the user approves it by number.
- *Settled, with a non-inferable rationale* → the card records the settled high-level conclusion in the managed `docs/design-rationale.md` now, with the one-line not-yet-in-code status, keeps any option the user weighed and overturned as a timeless `Rejected Alternatives` line (technical cause + revisit condition, zero timeline prose), and defers `docs/architecture.md`, `README.md`, and `AGENTS.md` to the **Post-Implementation Sync Checklist** (0 premature writes).
- *Settled, with no non-inferable rationale* → Option A (default) outputs the **Post-Implementation Sync Checklist** in chat with **0 file writes**, and `docs/design-rationale.md` stays untouched. In the **managed-map variant**, the card also offers Option B: rewrite the managed `docs/architecture.md` to the settled target now, explicitly listing the modules not yet in code. In the **unmarked-map variant**, Option A adds a checklist note that `docs/architecture.md` is currently unmarked and the user should confirm enrollment or sibling creation after the code lands, and the card's Option B item is the Section 4 3-way `① 纳管现有 docs/architecture.md / ② 另建受管文件 docs/architecture-overview.md / ③ 跳过保持不纳管` choice, with 0 writes to the unmarked file unless it is enrolled.
- *Landed diff against a managed map* → when the diff alters any one of the four — a macro module/layer boundary, a one-way dependency direction, a cross-module core business/runtime flow, or a system-wide invariant — Trigger 2 fires in the same turn and updates only the affected high-level section in place, at module-interaction altitude (no function call stacks). The subagent's cross-module flow reroute is evaluated by the interactive primary agent before it reports completion.
- *Unmarked map* → even when a landed diff alters a macro boundary, Trigger 2 stays **100% silent: 0 cards, 0 writes**, and the unmarked `docs/architecture.md` is left byte-identical.
- *Boundary unchanged* → report exactly `宏观架构边界未变，架构文档保持 0 修改`; `docs/architecture.md` gets 0 edits.
- *Convergence triggers* → both piggyback a one-screen numbered Change Card at the end of the same reply, with 0 extra pre-ask turns.
- *Subagent / headless run* → 0 auto-trigger cards and 0 writes; an explicit invocation prints the card and still writes nothing.
- *Approval binding* → an approval reply applies only when the card was the immediately preceding agent message and the sole pending question, or when the user explicitly names the card; otherwise the card expires with 0 writes and is re-presented before any write.
- Create **0** per-feature spec/task files.

### Pass criteria

- [ ] Before settlement: 0 files changed; any evidence gap is tagged `[待用户确认]`, never silently written.
- [ ] With rationale: only the managed `docs/design-rationale.md` is written — the settled conclusion in place with its one-line not-yet-in-code status; no scattered `[Proposed]` / `[Planned]` marker, no changelog; the seeded overturned shortcut appears under `Rejected Alternatives` with its technical cause, a revisit condition, and no dates or migration prose. The without-rationale variant leaves `docs/design-rationale.md` untouched and produces no `Rejected Alternatives` entry.
- [ ] Without rationale: 0 file writes; the Post-Implementation Sync Checklist appears in chat. In the managed-map variant, Option B on the card lists the modules not yet in code. In the unmarked-map variant, Option A's checklist notes the unmarked status and Option B is the 3-way enroll / sibling-create / skip item, with 0 writes to the unmarked file unless it is enrolled.
- [ ] Landed cross-module flow change against the managed map: the affected section is updated in place in the same turn, and the four-part boundary definition (module/layer boundaries, one-way dependency directions, cross-module core business/runtime flows, system-wide invariants) is used to decide whether Trigger 2 fires.
- [ ] Unmarked map (Trigger 2 auto-trigger): 0 cards, 0 writes, and the file stays byte-identical even when the landed diff alters a macro boundary (Trigger 2 silenced).
- [ ] The boundary-unchanged variant reports the exact line `宏观架构边界未变，架构文档保持 0 修改` and leaves the map untouched.
- [ ] Both convergence triggers produce a same-turn card with 0 extra pre-ask turns; subagent/headless runs produce 0 auto-trigger cards; a stale approval expires with 0 writes.
- [ ] README/AGENTS updates appear only in the Post-Implementation Sync Checklist in every branch; in the **managed-map variant** Option B approval unlocks only the managed `docs/architecture.md` rewrite to the settled target (listing the modules not yet in code), while in the **unmarked-map variant** it unlocks only the enrollment / sibling / skip choice and never a direct rewrite of the unmarked file. Neither Option B path licenses a premature README/AGENTS write.
- [ ] No per-feature spec or task file is created.

## QS6 — Sentinel Anti-Spoofing & Existing Doc Suites Stay Untouched

### Scenario

A developer runs a Path 2 audit on a large repository that already maintains its own design and architecture documentation, then asks to record why one mechanism exists. The repository exercises the sentinel's anti-spoofing rules: an `AGENTS.md` whose sentinel sits immediately after YAML frontmatter, and arc42 `docs/architecture.md` variants where the sentinel appears only inside a fenced code block or after the `# Title` heading.

### Seeded repo

- `AGENTS.md` opens with a YAML frontmatter block, then `<!-- eng-doc-guard:managed -->` as the first non-empty line after the frontmatter.
- Two arc42-style `docs/architecture.md` variants, neither following this skill's archetype: in one the `<!-- eng-doc-guard:managed -->` text appears only inside a fenced code block on line 15; in the other it sits on line 3 after a `# Title` heading.
- `docs/adr/0001-*.md` through `docs/adr/0012-*.md` and a `docs/design/` folder with several design docs, one of which contains past-tense history.
- `README.md` exists; no `docs/design-rationale.md`.
- A standalone non-governed topic reference doc `docs/deployment.md` is linked from `README.md` and contains field reference tables plus one paragraph repeating macro architecture prose; it sits outside the four governed roles' alias lists.
- A `README.md` fold variant: `README.md` carries an exhaustive CLI usage block of which half is already accurately carried in an existing unmarked `docs/cli.md` (matching the current code-backed CLI contract) and half is net-new.
- The mechanism's motive appears only in code, comments, and the foreign design docs; the user has not stated or confirmed it in the conversation.

### Expected response

- `AGENTS.md` is recognized as **managed** because the sentinel is the first non-empty line after the optional YAML frontmatter; it is audited and, if edited, keeps `<!-- eng-doc-guard:managed -->` in its managed position — the first non-empty line after the YAML frontmatter.
- Both arc42 `docs/architecture.md` variants are **unmanaged** (0 false matches): a sentinel inside a fenced code block or after a `# Title` heading never marks a file managed.
- ADRs, `docs/design/*`, and the foreign design docs get **0 edits**; any observations about them (including the past-tense history) appear only as advisory notes in chat, never as numbered card items that write or enroll.
- Because the arc42 `docs/architecture.md` is an unmarked governed document at a governed alias, offer the 3-way `Ask User` item — `[变更 N · 纳管 | 三选一：① 纳管现有 docs/architecture.md（首行写入 <!-- eng-doc-guard:managed --> 并按规则整理） / ② 不动原文件，另建受管文件 docs/architecture-overview.md（首行写入 <!-- eng-doc-guard:managed -->） / ③ 跳过保持不纳管（仅参考建议，0 写入）]` — with **0 writes unless enrolled**. Any proposed cleanup item on that file declares `[依赖变更 N]`, so skipping or excluding `N` skips them transitively with 0 writes.
- Recording the mechanism's motive does not auto-create a file and is never derived from code, comments, tests, or the foreign design docs: because no user confirmation exists in the conversation, the motive is one indivisible `Ask User (Confirm motive vs. Drop)` item tagged `[待用户确认]`.
- If the user confirms the motive and no rationale file exists, the card offers `Ask User` (`新建受管 docs/design-rationale.md（首行写入 <!-- eng-doc-guard:managed -->）并记录` vs. `跳过`).
- `docs/deployment.md` is a legitimate standalone non-governed topic reference doc: the Change Card carries **0 enrollment (`纳管`) items, 0 full-file delete (`Drop`) items, and 0 direct audit/rewrite items** for it; the paragraph inside it repeating macro architecture prose is mentioned only as an advisory observation in chat, identical to `docs/adr/*`.
- In the `README.md` fold variant against `docs/cli.md`: the exhaustive usage lines already carried in `docs/cli.md#<section>` and matching the current code-backed CLI contract are `Drop`ped from `README.md` under `§8 item 1(a)`; only the net-new lines are appended to `docs/cli.md` via one card-approved, non-enrolling `Move to Existing Doc` item — 0 `<!-- eng-doc-guard:managed -->` writes to `docs/cli.md`, and its existing content is neither audited nor deleted. `README.md` keeps representative examples and a link-out.
- `README.md` is audited normally.

### Pass criteria

- [ ] The post-frontmatter sentinel is recognized as managed, and any edit keeps `<!-- eng-doc-guard:managed -->` in its managed position — the first non-empty line after the YAML frontmatter.
- [ ] Sentinel occurrences inside a fenced code block or after the `# Title` heading produce 0 false managed matches and are treated as unmarked.
- [ ] No file under `docs/adr/` or `docs/design/` is created, edited, or deleted, and foreign suites never appear as write or enrollment items on the card.
- [ ] The unmarked arc42 `docs/architecture.md` triggers exactly the 3-way `Ask User` item (enroll existing / create `docs/architecture-overview.md` / skip), which discloses the line-1 sentinel write for the enroll and sibling options and produces 0 writes unless approved.
- [ ] Dependent cleanup items on the unmarked file declare `[依赖变更 N]`; declining or excluding `N` skips them with 0 writes.
- [ ] The mechanism motive is offered as `Ask User (Confirm motive vs. Drop)` tagged `[待用户确认]`; nothing is written from code, comments, tests, or existing prose.
- [ ] No duplicate decision record is created without the user choosing it.
- [ ] Any skill-owned new file uses a non-colliding alias and discloses the line-1 `<!-- eng-doc-guard:managed -->` write.
- [ ] `docs/deployment.md` receives 0 enrollment (`纳管`) items, 0 full-file delete (`Drop`) items, and 0 direct audit/rewrite items on the Change Card; its repeated macro-architecture prose is noted only as advisory chat, never as a numbered card item.
- [ ] In the fold variant, the already-carried matching lines are `Drop`ped from `README.md` citing `docs/cli.md#<section>` under `§8 item 1(a)`, only the net-new lines are appended via one card-approved, non-enrolling `Move to Existing Doc`, and `docs/cli.md` receives 0 `<!-- eng-doc-guard:managed -->` writes with no audit or deletion of its existing content.

## QS7 — Distillation Without Over-Pruning

### Scenario

A developer refreshes an existing, managed `docs/design-rationale.md` and `docs/architecture.md` after the codebase has grown and changed.

### Seeded repo

`docs/design-rationale.md` contains:

- an entry for a cache-warming mechanism whose code has been deleted;
- two entries that justify the same original need with slightly different wording;
- an entry explaining a constant that a code comment already explains;
- an `Open Ideas` item that has since landed in code;
- a long but valid entry for a non-obvious, cross-file invariant that is still in code;
- a section written as a TopicDock-style discussion log — `[C1]` / `[R2]` / `[Q3]` / `[A4]` item tags, hop numbers (`H020`), timestamps, and step-by-step debate narration;
- a paragraph written in telegraphic AI-speak with an unexplained project-specific domain term (for example "以「抓手」赋能同步链路" describing sync without ever explaining the term);
- a key reference already written as `[Title](URL) — summary of the borrowed insight`;
- an unconfirmed legacy motive that appears only in the file, with no user confirmation in the conversation.

`docs/architecture.md` lists twelve small modules one by one — grouping into four coarse macro units `cli/`, `sync/`, `store/`, `auth/` — where four coarse groups with one example each would carry the same boundaries. Alongside the 12-module listing it seeds a separate 4-line coarse directory tree enumerating only `cli/`, `sync/`, `store/`, `auth/` (zero individual files, no intra-module subdirectories) and carrying an entry-path note.

Variants: (i) a repo where that 4-line coarse macro tree is the sole enumeration of the macro units named in the responsibility/dependency prose (no module list or table in the document); (ii) a directory tree descending into internal subdirectories (`src/sync/internal/queue/`) or listing `.ts` files.

### Expected response

A Change Card with these distillation items:

| Seeded item | Disposition | Kept? |
|---|---|---|
| Entry for deleted cache-warming code | `Drop` (cites the code site proving removal) | evicted |
| Two same-need entries | `Merge` into one entry | merged |
| Entry duplicating a code comment | `Drop` (inferable from code) | evicted |
| Landed `Open Ideas` item | `Drop`, or promoted into an entry if its motive passes the admission test | evicted or promoted |
| Long valid invariant entry | `[保留]` (still passes its admission test) | kept |
| Telegraphic AI-speak paragraph with an unexplained domain term | `Rewrite in Place` (`改写/补释`): strip the AI filler and ledger shorthand, add a first-use plain-language gloss of the term | kept, rewritten |
| Twelve-module listing | `Merge` into four coarser groups, each with one example (item `M`) | lifted |
| Redundant 4-line coarse macro tree (`cli/`, `sync/`, `store/`, `auth/` + entry-path note) | `Merge` into the four-group macro section declaring `[依赖变更 M]` on item `M`, folding the entry-path note into the single macro representation (never `Drop`ped under a blanket tree ban; transitively skipped if `M` is excluded) | merged |
| Sole-representation coarse macro tree (variant i) | `[保留]` (passes Iron Law #4: coarse nodes named in the prose, zero files, no intra-module expansion) | kept |
| Deep/file-level directory tree (variant ii) | `Drop` (Iron Law #4: lists files or descends into internal subdirectories without a distinct macro boundary) | evicted |
| Discussion log with item tags, hop numbers, and debate narration | `Drop` the process traces; keep one distilled conclusion | distilled |
| Key reference in `[Title](URL) — summary` form | `[保留]` (already the required shape) | kept |
| Unconfirmed legacy motive | `Ask User (Confirm motive vs. Drop)` tagged `[待用户确认]` | pending confirmation |

### Pass criteria

- [ ] Every distillation candidate appears as a numbered card item; nothing is pruned silently.
- [ ] The still-valid invariant entry is kept; length alone never justifies `Drop`.
- [ ] The telegraphic AI-speak paragraph is rewritten in place via `Rewrite in Place` (`改写/补释`) with a first-use definitional gloss, not dropped.
- [ ] Merges preserve every fact that still passes its admission test.
- [ ] No fixed numeric line or entry cap is cited as a reason.
- [ ] Discussion-log traces (item tags, hop numbers, timestamps, debate narration) are gone; only the distilled conclusion remains.
- [ ] The key reference keeps its `[Title](URL) — summary` shape and is not dropped.
- [ ] The unconfirmed motive is offered for confirmation and never written from code or existing prose.
- [ ] The 12-module listing is `Merge`d into four coarser macro groups (item `M`), preserving every module fact that still passes its admission test.
- [ ] The redundant 4-line coarse macro tree is `Merge`d into that section declaring `[依赖变更 M]`, folding its entry-path note into the single macro representation; it is never `Drop`ped under a blanket tree ban, and it is skipped transitively with 0 writes when `M` is excluded.
- [ ] In variant (i), the sole-representation coarse macro tree is `[保留]` — it passes Iron Law #4 as the sole enumeration of the macro units named in the responsibility/dependency prose.
- [ ] In variant (ii), the deep/file-level tree (internal subdirectories like `src/sync/internal/queue/` or listed `.ts` files) is `Drop`ped under Iron Law #4, citing pace layering rather than code readability.
