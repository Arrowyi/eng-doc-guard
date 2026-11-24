<!-- eng-doc-guard:managed -->
# eng-doc-guard

An agent skill that keeps a repository's top-level engineering documents small, accurate, and grounded in the code, records *why* the project's key design decisions were made, and never changes a document without your approval.

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
| `docs/architecture.md` | The macro shape of the system: layers, module boundaries, dependency rules, cross-module flows, and system-wide invariants |
| `docs/design-rationale.md` | Distilled design inspirations, core decisions, and key reference summaries, plus ideas you asked to keep |

All four documents stay distilled: they grow much more slowly than the code, and every run proposes merging or removing entries that no longer earn their place. If your repo already has ADRs or its own design or architecture docs, the skill only makes suggestions about them and uses non-colliding names for its own files.

Four iron laws decide what stays in them:

- **1. Information hiding (`README.md`).** Keep a fact only if an external user needs it to evaluate, install, invoke, or trust the software without reading its source.
- **2. Non-inferable single source of truth (`AGENTS.md`).** Keep only what an agent would get wrong on its first try or spend many steps rediscovering. That means non-default conventions, co-change rules, "never do X" invariants, and the `Change -> Verification` map. Directory trees and facts readable from manifests are evicted. There is one canonical file (`AGENTS.md` or `CLAUDE.md`); when both are needed for multi-agent compatibility, the other shrinks to a two-line pointer file — the invisible ownership marker `<!-- eng-doc-guard:managed -->` on line 1 and `@AGENTS.md` on line 2.
- **3. Current state, settled decisions, and ideas you asked to record.** History belongs to Git. Docs are rewritten in place. A settled decision that is not built yet is recorded with a "not yet in code" note, and an overturned option survives only as a timeless rejected alternative. Unsettled discussion produces zero file writes unless you explicitly ask to keep it as an open idea.
- **4. Slow-changing macro altitude (`docs/architecture.md`).** The architecture map exists so a person can hold the whole system in their head without reading every source file, so it is intentionally allowed to restate what the code shows. It keeps only the slow-moving shape — system context, module responsibilities, dependency directions, cross-module flows, and system invariants — and leaves fast-changing implementation detail to the code.

Nothing here is a fixed section count or a line limit. The skill uses a few plain questions instead — who reads this document and what one question must it answer, what a fact must survive to stay, which sections genuinely fit this repo, and where the hard boundaries are — so the shape adapts to your project rather than forcing every project into the same template.

Three of these documents are read by people, so they are written as natural prose, and the first time a project-specific term appears it gets a short plain-language explanation. `AGENTS.md` is the exception: it is read by coding agents, so it stays dense and command-focused.

**Ownership is opt-in.** The skill only touches documents it created or that you explicitly enroll. A document is enrolled when its first line is the HTML comment `<!-- eng-doc-guard:managed -->` — a marker that renders invisibly and tells you, a diff, and the agent that this file is maintained by the skill. A document without that line is never quietly rewritten, and a code change alone never triggers a proposal on it. Every create, enroll, or edit is shown on the Change Card first, so you can decline; if your Markdown setup rejects HTML comments, you can keep the file un-enrolled, and you can opt out at any time by deleting the line.

`CHANGELOG.md` is out of scope: never audited, never generated.

## Workflows

- **Single-doc write / refresh.** Write or clean up one named document.
- **Repo-wide audit.** Reports leaks, duplication, historical noise, and drift, then recommends only the docs your repo needs. If your docs are already sound, it says so and changes nothing.
- **Decision sync.** Records a newly settled decision in `docs/design-rationale.md` — with the reason, when you have confirmed it — and defers other docs until the code lands.

**Routine silence, two convergence points.** It stays silent during pure coding or debugging turns, code-comment and commit-message edits, and reader-facing writing under `userdoc/`. It speaks at exactly two convergence points — when you settle a high-level design inspiration, methodology reference, or paradigm decision, and when landed code (including a delegated coding agent's diff) changes the macro shape of an existing, enrolled architecture map: its major modules, dependency directions, cross-module flows, and system-wide invariants — piggybacking a one-screen Change Card on the same reply; a repo with no architecture map, or an unenrolled one, gets no such card; subagent and headless runs emit no trigger cards. It never injects standing guidance blocks into your `AGENTS.md` or `CLAUDE.md`.

## Consent: the Change Card

Every edit, move, creation, deletion, or enrollment waits behind a one-screen numbered Change Card. Nothing is written until you reply. An approval applies to the card shown in the immediately preceding reply, or to an earlier card you explicitly name; a card the conversation has moved past expires with zero writes and is shown again before anything is written.

The card's header tags are in Chinese. `[保留]` ("kept") lists what stays as-is. Each numbered `[变更 N]` ("change N") is one proposed change: its action (for example `删除`, "delete", or `纳管`, "enroll"), then after the `|` the reason, such as `铁律 #1` ("Iron Law 1"). The last line (`回复`, "reply") lists your options. An abridged card:

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

Requires Python 3.9 or newer and git. One line, no clone:

```bash
curl -fsSL https://raw.githubusercontent.com/Arrowyi/eng-doc-guard/main/scripts/install.sh | bash -s -- --client opencode   # or: claude | cursor | codex | all
```

Or clone this repository and run one of these from the checkout:

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
- "Record in the design rationale the inspiration behind this design decision."

## Further reading

- [`references/examples.md`](references/examples.md): worked before/after examples of how the rules apply.
- [`docs/design-rationale.md`](docs/design-rationale.md): why this skill works the way it does.
- [`AGENTS.md`](AGENTS.md): repository maintainer guide.
