# eng-doc-guard

An agent skill that keeps a repository's top-level engineering documents small, accurate, and grounded in the code, records *why* the project's mechanisms exist, and never changes a document without your approval.

It is a lightweight guard, not a process framework: it does not make your project follow a spec, and it leaves documentation suites you already maintain untouched.

## Why it exists

Project docs go wrong in three ways, whether a person or a coding agent maintains them:

1. **Docs bloat and lose their boundaries.** `README.md` fills with implementation details no outside reader needs. `AGENTS.md` and `CLAUDE.md` turn into duplicate copies full of static directory trees. Changelogs creep into current-state docs, and statements drift away from the code.
2. **Agents write too freely or too early.** Files are edited silently, build commands are guessed, and half-settled brainstorming lands in docs that should describe what is true now.
3. **The reasons get lost.** Months later nobody remembers what a rule or workflow was for, so it is either kept out of fear or removed and the original problem returns.

## What it governs

Four current-state documents, offered as an opt-in menu sized to your repo. It recommends nothing by default.

| Document | Role |
|---|---|
| `README.md` | Landing page for outside users |
| `AGENTS.md` / `CLAUDE.md` | Operating notes for coding agents |
| `docs/architecture.md` | Where things live: layers, module boundaries, dependency rules, and where to look for a given change or problem |
| `docs/design-rationale.md` | Why mechanisms, rules, and workflows exist, when to revisit them, and ideas you asked to keep |

The two `docs/` files stay distilled: they grow much more slowly than the code, and every run proposes merging or removing entries that no longer earn their place. If your repo already has ADRs or its own design or architecture docs, the skill only makes suggestions about them and uses non-colliding names for its own files.

Three iron laws decide what stays in them:

- **1. Information hiding (`README.md`).** Keep a fact only if an external user needs it to evaluate, install, invoke, or trust the software without reading its source.
- **2. Non-inferable single source of truth (`AGENTS.md`).** Keep only what an agent would get wrong on its first try or spend many steps rediscovering. That means non-default conventions, co-change rules, "never do X" invariants, and the `Change -> Verification` map. Directory trees and facts readable from manifests are evicted. There is one canonical file (`AGENTS.md` or `CLAUDE.md`), with at most a one-line `@AGENTS.md` pointer in the other.
- **3. Current state, settled decisions, and ideas you asked to record.** History belongs to Git. Docs are rewritten in place. A settled decision that is not built yet is recorded with a "not yet in code" note, and an overturned option survives only as a timeless rejected alternative. Unsettled discussion produces zero file writes unless you explicitly ask to keep it as an open idea.

`CHANGELOG.md` is out of scope: never audited, never generated.

## Workflows

- **Single-doc write / refresh.** Write or clean up one named document.
- **Repo-wide audit.** Reports leaks, duplication, historical noise, and drift, then recommends only the docs your repo needs. If your docs are already sound, it says so and changes nothing.
- **Decision sync.** Records a newly settled decision, and the reason for it, in `docs/design-rationale.md`, and defers other docs until the code lands.

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
- "Record in the design rationale why this workflow exists."

## Further reading

- [`references/examples.md`](references/examples.md): worked before/after examples of how the rules apply.
- [`docs/design-rationale.md`](docs/design-rationale.md): why this skill works the way it does.
- [`AGENTS.md`](AGENTS.md): repository maintainer guide.
