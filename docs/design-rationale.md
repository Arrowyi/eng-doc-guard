# Design Rationale

Why eng-doc-guard works the way it does: the high-level inspirations, the settled decisions they produced, and the methodology it borrowed. Read the matching section before changing a mechanism or paradigm it covers, and rewrite it in place when that mechanism or paradigm changes.

## A lightweight boundary guard, not a process framework

eng-doc-guard audits, proposes, and records; it never makes a project conform to a spec, a phase, or a workflow. Adoption has to stay cheap for teams of any size and style, so the skill is advisory toward documentation a project already maintains: foreign design, architecture, and decision suites get chat suggestions, never edits. The accepted cost is that it cannot enforce documentation discipline the way heavier tooling does — it protects boundaries and records intent, and leaves compliance to the team.

Rejected alternative: spec-driven per-feature process frameworks — not used because they turn a documentation aid into mandatory process every contributor must follow. Revisit only if users consistently ask for enforced gates.

## One reader question per document, two provenance rules

Each governed document answers a single reader question, so a fact lives in exactly one obvious place:

- `README.md` — can an outside user evaluate, install, and invoke this software?
- `AGENTS.md` — which non-obvious facts would a coding agent otherwise get wrong?
- architecture map — what is the macro structure: which units exist, what each owns and does not own, and which way dependencies run?
- design rationale — why do the settled high-level choices, paradigms, and references exist?

The two maintainer-facing documents answer those questions under different provenance rules. The architecture map may be synthesized from inspected code once a repo has at least three decoupled modules, because macro boundaries and dependency directions are visible in the code. The design rationale is human-originated only: code may confirm that a mechanism exists, but code, the document under audit, and agent-generated artifacts can never supply its motive, inspiration, or reference lineage — only the user's own statement or confirmation counts. This non-circular provenance gate is why unconfirmed legacy prose is routed to the user for a confirm-or-drop decision instead of being verified by the agent itself. The accepted cost is that a motive we could plausibly infer stays unrecorded until someone states it.

Revisit if a recurring kind of fact fits none of the four questions.

## If it's in code, don't record it — distill by principle, not by numbers

Reasons local to one file or one mechanism belong in a 1–3 line source comment next to the code. The documents keep the high-level layer — boundaries, dependency directions, system invariants, and the reasoning behind them — never per-mechanism detail a reader can recover from the code. As the codebase grows, entries merge or lift to a coarser level instead of multiplying, so a document settles at a size made of essentials; an entry that still earns its place is never dropped for length. Size is controlled by principles, never by numeric caps, because any number is wrong for some project and invites deleting valid content to meet it.

Rejected alternatives: a per-mechanism entry template that forces every mechanism into the same need/approach/cost sentence — not used because it induces white-box code narration and post-hoc motives; and fixed line or entry caps — not used because they reward deletion over distillation. Revisit if a document still bloats while every entry passes its admission test.

## Same-turn convergence cards for turn and token efficiency

The skill stays 100% silent during routine coding, debugging, comment and commit edits, and in-module changes that leave macro boundaries alone. It speaks at exactly two convergence points, and it piggybacks a one-screen numbered Change Card onto the same reply instead of spending an extra pre-ask turn: when the user explicitly settles a high-level inspiration, methodology reference, or paradigm decision; and when landed code alters C4 L1–L2 macro boundaries in an existing architecture map — including a coding subagent's diff, which the interactive primary agent evaluates before reporting completion. Consent stays fail-closed: an approval authorizes a card only when that card was the immediately preceding message and the sole pending question; otherwise the card expires with zero writes and must be re-presented. Subagent and headless runs never emit trigger cards, and an explicit invocation there writes nothing. The accepted cost is one extra round-trip per card, which is the price of never writing a document the user did not approve.

Revisit if users ask for a trusted auto-apply mode for specific change types.

## Strict artifact ownership, in documents and in the installer

The skill owns only the files it created or that already follow its archetype; everything else is audited and advised, never taken over. The installer follows the same rule mechanically: it touches only manifest-managed skill roots and sentinel-marked command files, never a user's global agent instruction file outside those roots. The accepted cost is that a hand-edited install blocks an upgrade until the user resolves it.

Revisit if clients ship a native package manager that supersedes manifest-tracked installs.

## Key References

- [ARCHITECTURE.md — matklad](https://matklad.github.io/2021/02/06/ARCHITECTURE.md.html) — Record only what is unlikely to change often; boundaries and a coarse structural map beat detailed per-module walkthroughs.
- [Design Rationale Systems: Understanding the Issues — Jintae Lee, IEEE Intelligent Systems 12(3), 1997, DOI 10.1109/64.592267](https://www.computer.org/csdl/magazine/ex/1997/03/x3078/13rRUwhpBHf) — The classic map of design-rationale capture issues; the source of the warning that rationale reconstructed post-hoc from artifacts loses the original reasoning.
- [Integrating different perspectives on design rationale — Shipman & McCall, AI EDAM 11(2), 1997](https://doi.org/10.1017/S089006040000192X) — Rationale emerges incrementally from design communication; we borrowed the distillation of settled communication into structured conclusions and rejected the heavy discussion-record form.
- [Evaluating AGENTS.md: Are Repository-Level Context Files Helpful for Coding Agents? — Gloaguen et al., ETH Zurich & LogicStar.ai, arXiv:2602.11988](https://arxiv.org/abs/2602.11988) — Context files raised inference cost by more than 20% without improving task success, and repository overviews were the unhelpful part; the empirical basis for keeping `AGENTS.md` to non-inferable facts.
- [Best practices for Claude Code — Anthropic](https://www.anthropic.com/engineering/claude-code-best-practices) — The practitioner-side rule that the agent reads the repository itself, so a context file should hold only what is not inferable from it.
- [Documenting Architecture Decisions — Michael Nygard, 2011](https://cognitect.com/blog/2011/11/15/documenting-architecture-decisions) — The ADR pattern this skill deliberately contrasts: immutable, append-only records force reconstructing the current answer from a chain of superseded ones.
- [Diátaxis](https://diataxis.fr/) — Documentation forms organized by reader need; the inspiration for one question per document and the opt-in menu.
