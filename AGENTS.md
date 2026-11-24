<!-- eng-doc-guard:managed -->
# eng-doc-guard Maintainer Guide

This checkout is the single source of truth for everything the installer ships. Installed roots are build artifacts: never hand-edit them or their `.managed-by-eng-doc-guard.json` manifest.

## Source-of-truth layout

| Repo file | Role / where it lands |
|---|---|
| `SKILL.md` + `references/examples.md` | Skill payload, copied verbatim into each installed skill root; agents load `references/` on demand |
| `scripts/templates/eng-doc-guard.md` | Slash-command template; copied into the opencode/claude command dirs (sentinel line must sit immediately after the frontmatter, body ≤15 non-empty lines) |
| `scripts/install.py`, `scripts/install.sh` | Installer and its POSIX wrapper (`install.sh` runs `install.py` from `$ENG_DOC_GUARD_SRC_DIR`, or from a shallow git fetch of `$ENG_DOC_GUARD_REMOTE`) |
| `tests/test_install.py`, `tests/acceptance-fixtures.md` | Dev-only installer suite and manual skill-behavior fixtures; never shipped to installed roots |
| `README.md`, `AGENTS.md`, `docs/design-rationale.md` | Repo docs, never shipped; subject to the skill's own audit |

Every installed skill root carries the manifest; the suite verifies payload hashes, manifest content, and the command sentinel.

Before changing a mechanism of the skill or the installer's manifest and sentinel ownership, read [`docs/design-rationale.md`](docs/design-rationale.md) for the high-level inspirations and settled conclusions behind these mechanisms:

- **Four iron laws** — #1 information hiding / version-stability black-box test (`README.md`); #2 non-inferable single source of truth (`AGENTS.md` / `CLAUDE.md`); #3 current state, settled decisions, and recorded intent only (history belongs to git); #4 slow-changing macro altitude / Pace Layering (`docs/architecture.md`, explicitly exempt from #2), keeping slow-changing macro structure (including coarse macro-module directory layouts, merged when duplicating an in-doc module table) while evicting fast-changing file/symbol lookup inventories.
- **Ownership sentinel** — `<!-- eng-doc-guard:managed -->` on line 1 marks a managed doc; unmarked existing docs are never edited without an explicit enrollment (纳管) item approved on the Change Card.
- **Seven-way dispositions & card action vocabulary** — content dispositions (Drop / Fold / Merge / Rewrite in Place / Move to Existing Doc / Ask User: Drop vs. Create & Move / Ask User: Confirm motive vs. Drop) rendered through the one-screen numbered Change Card action vocabulary (纳管 / 新建 / 删除 / 折叠 / 合并 / 改写/补释 / 迁移, plus the pending actions 待补 / 待决 / 待确认).
- **Silence boundary & marker-aware convergence triggers** — routine intra-module coding/debugging turns stay 100% silent; the architecture trigger fires ONLY on a managed Architecture Map, and a landed change counts as a boundary change when it alters any of: C4 L1–L2 macro module/layer boundaries, one-way dependency directions, cross-module core business flows, or system-wide invariants.
- **Distillation & provenance gate** — keep every governed doc distilled to content that still passes admission; record a design rationale motive only from explicit user confirmation, never reverse-engineered from code.

When the user settles a high-level design inspiration, methodology reference, or paradigm decision, propose synthesizing it in place into `docs/design-rationale.md` (with `eng-doc-guard` if available).

## Change → verification

| Change | Run |
|---|---|
| `SKILL.md`, `references/**` | Keep `docs/design-rationale.md` consistent in place (it holds high-level inspirations and conclusions, not per-mechanism entries), update the affected fixtures in `tests/acceptance-fixtures.md` and walk them by hand, then `python3 tests/test_install.py`; keep `SKILL.md` to rules only and move examples into `references/` |
| `scripts/install.py`, `scripts/install.sh`, `scripts/templates/**` | Full `python3 tests/test_install.py` + `bash -n scripts/install.sh` |
| `README.md`, `AGENTS.md`, `docs/**` | Dogfood audit against the skill's iron laws and distillation check + `python3 tests/test_install.py` (the in-suite portability scan covers them) |

## Update together

- `VERSION` in `scripts/install.py` and the manifest `version` assertion in `tests/test_install.py`; bump it whenever the shipped payload changes behavior.
- `PAYLOAD_FILES` in `scripts/install.py` and in `tests/test_install.py`.

## Prohibitions

- Never hand-edit an installed root or its manifest; local edits abort the next install until `--force`.
- Never commit developer-machine paths; `SKILL.md`, `references/`, `scripts/`, `docs/`, `README.md`, and `AGENTS.md` stay 100% portable.
- The repo's governed docs (`README.md`, `AGENTS.md`, `docs/design-rationale.md`) carry the first-line `<!-- eng-doc-guard:managed -->`; keep it on line 1 when editing them.
- Never touch the command sentinel: it must remain immediately after the frontmatter, and the template body stays within the suite's line cap.

## Publish checklist

1. Confirm `ENG_DOC_GUARD_REMOTE` in `scripts/install.sh` still points to the canonical repo URL (`ENG_DOC_GUARD_REF` defaults to `main`).
2. Tag the release.
3. Run the full suite and `bash -n scripts/install.sh`.
4. Self-install proof: `python3 scripts/install.py --client opencode`, then verify the installed root (manifest present, `SKILL.md` byte-identical to the checkout, command sentinel intact).
5. Only then add the `curl | bash` one-liner with the canonical URL to `README.md`; until then the README intentionally shows only the clone-and-run form.

## Known behavior

A multi-root run that fails at root 2 after root 1 was swapped leaves mixed versions; there is no rollback by design. The next no-arg lockstep run heals every root in lockstep.

## Runtime floor

Python ≥ 3.9 (the suite runs on 3.9 exactly). POSIX (macOS/Linux) is the reference platform; native Windows is best-effort — `os.replace` swap semantics, age-based stale-lock recovery only.
