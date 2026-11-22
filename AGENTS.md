# eng-doc-guard Maintainer Guide

This checkout is the single source of truth for everything the installer ships. Installed roots are build artifacts: never hand-edit them or their `.managed-by-eng-doc-guard.json` manifest.

## Source-of-truth layout

| Repo file | Role / where it lands |
|---|---|
| `SKILL.md` + `references/examples-and-audit-checklist.md` | Skill payload, copied verbatim into each installed skill root |
| `scripts/templates/eng-doc-guard.md` | Slash-command template; copied into the opencode/claude command dirs (sentinel line must sit immediately after the frontmatter, body ≤15 non-empty lines) |
| `scripts/install.py`, `scripts/install.sh` | Installer and its POSIX wrapper (`install.sh` runs `install.py` from `$ENG_DOC_GUARD_SRC_DIR`, or from a shallow git fetch of `$ENG_DOC_GUARD_REMOTE`) |
| `tests/test_install.py` | Dev-only suite; never shipped to installed roots |
| `README.md`, `AGENTS.md` | Outside-facing and maintainer docs, subject to the skill's own audit |

Every installed skill root carries the manifest; the suite verifies payload hashes, manifest content, and the command sentinel.

## Change → verification

| Change | Run |
|---|---|
| `SKILL.md`, `references/**` | Review the fixture diff against `references/examples-and-audit-checklist.md`, then `python3 tests/test_install.py` (fixture-integrity + line-budget tests cover them) |
| `scripts/install.py`, `scripts/install.sh`, `scripts/templates/**` | Full `python3 tests/test_install.py` + `bash -n scripts/install.sh` |
| `README.md`, `AGENTS.md` | Dogfood audit against the skill's iron laws + `python3 tests/test_install.py` (the in-suite portability scan covers both) |

## Prohibitions

- Never hand-edit an installed root or its manifest; local edits abort the next install until `--force`.
- Never commit developer-machine paths; shipped artifacts (`SKILL.md`, `references/`, `scripts/`, `README.md`, `AGENTS.md`) stay 100% portable.
- Never touch the command sentinel: it must remain immediately after the frontmatter, and the template body stays within the suite's line cap.

## Publish checklist

1. Set `ENG_DOC_GUARD_REMOTE` in `scripts/install.sh` to the canonical repo URL (`ENG_DOC_GUARD_REF` defaults to `main`).
2. Tag the release.
3. Run the full suite and `bash -n scripts/install.sh`.
4. Self-install proof: `python3 scripts/install.py --client opencode`, then verify the installed root (manifest present, `SKILL.md` byte-identical to the checkout, command sentinel intact).
5. Only then add the `curl | bash` one-liner with the canonical URL to `README.md`; until then the README intentionally shows only the clone-and-run form.

## Known behavior

A multi-root run that fails at root 2 after root 1 was swapped leaves mixed versions; there is no rollback by design. The next no-arg lockstep run heals every root in lockstep.

## Runtime floor

Python ≥ 3.9 (the suite runs on 3.9 exactly). POSIX (macOS/Linux) is the reference platform; native Windows is best-effort — `os.replace` swap semantics, age-based stale-lock recovery only.
