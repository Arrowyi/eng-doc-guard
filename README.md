# eng-doc-guard

An agent skill that keeps a repository's top-level engineering documents small, accurate, and grounded in the code, and never changes them without your approval.

## Why it exists

Project docs go wrong in two ways, whether a person or a coding agent maintains them:

1. **Docs bloat and lose their boundaries.** `README.md` fills with implementation details no outside reader needs. `AGENTS.md` and `CLAUDE.md` turn into duplicate copies full of static directory trees. Changelogs creep into current-state docs, and statements drift away from the code.
2. **Agents write too freely or too early.** Files are edited silently, build commands are guessed, and half-settled brainstorming lands in docs that should describe what is true now.

## What it governs

Four current-state documents, offered as an opt-in menu sized to your repo. It recommends nothing by default.

| Document | Role |
|---|---|
| `README.md` | Landing page for outside users |
| `AGENTS.md` / `CLAUDE.md` | Operating notes for coding agents |
| `ARCHITECTURE.md` (or `docs/architecture.md`) | Module structure and one-way dependency rules |
| Technical Design Doc (`docs/design*.md` or `docs/design/*.md`) | Settled decisions, trade-offs, rejected alternatives |

Three iron laws decide what stays in them:

- **1. Information hiding (`README.md`).** Keep a fact only if an external user needs it to evaluate, install, invoke, or trust the software without reading its source.
- **2. Non-inferable single source of truth (`AGENTS.md`).** Keep only what an agent would get wrong on its first try or spend many steps rediscovering. That means non-default conventions, co-change rules, "never do X" invariants, and the `Change -> Verification` map. Directory trees and facts readable from manifests are evicted. There is one canonical file (`AGENTS.md` or `CLAUDE.md`), with at most a one-line `@AGENTS.md` pointer in the other.
- **3. Current state and settled decisions only.** History belongs to Git. Docs are rewritten in place. An overturned option survives only as a timeless `Rejected Alternatives` entry in the design doc. Unsettled discussion produces zero file writes.

Architecture Decision Records (ADRs, under `docs/adr/`) and `CHANGELOG.md` are out of scope: never audited, never generated.

## Workflows

- **Single-doc write / refresh.** Write or clean up one named top-level document.
- **Repo-wide audit and right-sized menu.** Reports internal-detail leaks, duplication, historical noise, and code-vs-doc drift. It then right-sizes the set: `README.md` + `AGENTS.md` for small repos, `ARCHITECTURE.md` only at 3 or more decoupled modules, and a design doc only for non-trivial trade-offs. If your docs are already sound, it says so and changes nothing.
- **New-requirement / settled-design sync.** Once a design decision is settled, it folds the decision into the design doc in place. If the change moves architecture boundaries and the code has not landed yet, you choose: **Option A** (default) updates the design doc now and defers `ARCHITECTURE.md`, `README.md`, and `AGENTS.md` to a post-implementation checklist; **Option B** rewrites `ARCHITECTURE.md` to the settled target now, explicitly listing the modules not yet in code.

**Silence boundary.** It stays silent during pure coding or debugging turns, code-comment and commit-message edits, and reader-facing writing under `userdoc/`. It never adds wake-up blocks to your `AGENTS.md` or `CLAUDE.md`.

## Consent: the Change Card

Every edit, move, creation, or deletion waits behind a one-screen numbered Change Card. Nothing is written until you reply.

The card's header tags are in Chinese. `[保留]` ("kept") lists what stays as-is. Each numbered `[变更 N]` ("change N") is one proposed change: its action (for example `删除`, "delete"), then after the `|` the reason, such as `铁律 #1` ("Iron Law 1"). The last line (`回复`, "reply") lists your options. An abridged card:

```text
[保留] README.md install and quickstart; AGENTS.md Change -> Verification map
[变更 1 · 删除 | 铁律 #1: internal SQL clause in README]
[变更 2 · 删除 | 铁律 #3: past-tense version log in README]
回复 y / 只改 1,3 / 除 2 外 / 看 N
```

- `y`: apply everything.
- `只改 1,3`: apply only items 1 and 3.
- `除 2 外`: apply everything except item 2.
- `看 N`: expand the full text of item N.

A claim that cannot be traced to a repo file or to something you said is tagged `[待用户确认]` (pending your confirmation). It is never written until you confirm it. Headless, non-interactive, or subagent runs print the card and make **0 file writes**. In a directory without Git, the card adds a permanent-overwrite warning.

## Install

Requires Python 3.9 or newer. Clone this repository, then run one of these from the checkout:

```bash
python3 scripts/install.py --client opencode   # or: claude | cursor | codex | all
ENG_DOC_GUARD_SRC_DIR=<repo-checkout> bash scripts/install.sh --client all
```

The shell script is a wrapper around the same installer. Run `python3 scripts/install.py` with no `--client` to upgrade every globally installed client in lockstep.

| Flag | Effect |
|---|---|
| `--dry-run` | Preview what would happen without writing |
| `--force` | Overwrite local edits to installed files |
| `--uninstall` | Remove the managed skill and command files |
| `--project` | With `--client codex`, install per directory into `./.agents/skills/eng-doc-guard` |

POSIX (macOS and Linux) is the reference platform. Native Windows is best-effort.

## Quickstart

OpenCode and Claude Code get a slash command; Cursor and Codex pick the skill up by natural language.

```text
/eng-doc-guard [all | readme | agents | arch | design | sync]
```

With no argument it runs `all`. Or just ask:

- "Audit and clean up our top-level docs."
- "Refresh README.md."
- "Sync this settled design decision into docs/design.md."

## Further reading

- [`references/examples-and-audit-checklist.md`](references/examples-and-audit-checklist.md): worked before/after evictions and manual acceptance fixtures.
- [`AGENTS.md`](AGENTS.md): repository maintainer guide.
