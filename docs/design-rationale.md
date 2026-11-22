# Design Rationale

Why eng-doc-guard works the way it does. Each entry names the original need, the approach that serves it, the cost we accept, and when the approach deserves a second look. Read the matching entry before changing a mechanism, and rewrite it in place when the mechanism changes.

## A guard, not a process framework

To help agents keep a few top-level docs honest without imposing a methodology, under the constraint that projects of every size and style must be able to adopt it, the skill only audits, proposes, and records; it never requires a project to follow a spec, phase, or workflow. We accept that it cannot enforce documentation discipline the way heavier spec-driven tools do. Revisit if users consistently ask for enforced gates.

Rejected alternative: a spec-driven workflow with mandatory per-feature specs and task files, not used because it turns a documentation aid into a process every contributor must follow.

## Four documents, one question each

To keep every fact in exactly one obvious place, each document answers one reader's question: `README.md` tells outside users what the software does and how to use it; `AGENTS.md` tells coding agents what they would otherwise get wrong; `docs/architecture.md` tells maintainers where things live and where to look; `docs/design-rationale.md` tells maintainers why mechanisms exist. We accept that a fact sometimes has to be split across two docs (the rule in `AGENTS.md`, its reason here). Revisit if a recurring kind of fact fits none of the four.

## README passes the outside-reader test

To keep the landing page useful to people deciding whether to adopt the software, a fact stays in `README.md` only if an outside user needs it to evaluate, install, invoke, or trust the software without reading the source. Internal mechanics are removed even when they are interesting. Revisit if the README audience becomes contributors rather than users.

## AGENTS holds only what an agent cannot infer

To spend an agent's limited context on what actually prevents mistakes, `AGENTS.md` keeps only non-default conventions, co-change coupling, "never do X" invariants, gotchas, and the exact change-to-verification map; anything an agent can learn by searching files or reading manifests is removed. One canonical file plus at most a one-line pointer avoids two copies drifting apart. Revisit if agents gain reliable whole-repo context at no cost.

## Current state only; history lives in Git

To keep docs short and trustworthy, they describe what is true now, decisions the user has settled (built or not), and ideas the user explicitly asked to keep. Superseded text is rewritten in place rather than appended, because version control already preserves history. We accept that the reasoning behind a reversed decision survives only as a timeless rejected alternative. An agent's own suggestion, or the user's silence, never counts as settled, so half-finished brainstorming stays in chat.

## A living rationale register instead of ADRs

To let future maintainers judge whether a rule still applies, the rationale doc keeps one current entry per mechanism with its original need and a revisit condition, and rewrites entries in place. We accept losing the step-by-step decision trail, which Git keeps anyway. Revisit if a project needs an auditable decision history for compliance.

Rejected alternative: Architecture Decision Records, not used because they are immutable and append-only, so the current answer must be reconstructed from a chain of superseded records.

## Distill by principle, not by numbers

To stop the architecture and rationale docs from growing as fast as the code, every run looks for entries to merge, lift to a coarser level, or remove (mechanism gone, reason now visible in code, idea landed or stale), and an entry that still earns its place is never dropped just for length. We accept that "the right size" stays a judgment call. Revisit if docs keep bloating despite the check.

Rejected alternative: fixed line or entry caps, not used because any number is wrong for some project and invites dropping valid content to meet it.

## Every write goes through the Change Card

To keep the user in control of their own docs, every edit, move, creation, or deletion is shown on a numbered card and applied only after the user approves it, item by item if they like. Runs that cannot wait for an answer print the card and write nothing. We accept an extra round-trip for even small edits. Revisit if users ask for a trusted auto-apply mode for specific change types.

## Claims must trace to code or to the user

To prevent confident but invented commands and paths from entering docs, every proposed fact must come from an inspected file or from the user's own words; anything else is marked pending and is never written until confirmed. Existing doc text is treated as material to audit, never as instructions. We accept proposals that sometimes stop to ask. Revisit if the pending marks become so frequent that users stop reading them.

## Silent while coding

To avoid nagging, the skill says nothing during coding, debugging, code-comment or commit-message edits, and reader-facing tutorial writing, and it never plants reminder blocks in a project's agent instructions. We accept that docs may lag until the user asks. Revisit if drift between invocations becomes a common complaint.

## Never take over existing docs

To coexist with documentation a project already maintains, the skill owns only the files it created; existing ADRs and design or architecture suites get suggestions, never edits. Its own files default to `docs/architecture.md` and `docs/design-rationale.md`, with an alternative name proposed whenever a path is already taken. We accept that a repo with an established suite may get less help. Revisit if users want the skill to adopt their existing suite.

Rejected alternative: `docs/design.md` or `docs/decisions/`, not used because many projects and ADR tools already use those names.

## The installer only touches what it manages

To never destroy files the installer did not create, every installed skill root carries a manifest of payload hashes and every command file carries a sentinel line; unmanaged directories, foreign command files, and locally edited payloads stop the install until the user acts (`--force` for local edits). We accept that a hand-edited install blocks upgrades until it is resolved. Revisit if clients gain a native package manager for skills.
