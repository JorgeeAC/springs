# Skill: Autonomous Engineering Pass

Use this procedure when a human maintainer explicitly requests an extended autonomous improvement pass.

The human remains the architectural owner.

Your job is to strengthen the existing project direction, not redefine it.

---

# Before Starting

Read:

    AGENTS.md
    docs/agent-guide.md
    docs/session-handoff.md

Then inspect any relevant technical documentation.

Before changing code:

1. inspect the repository
2. check git status
3. identify the current branch
4. run the existing tests
5. run the existing demo when practical
6. understand the current working behavior

Prefer performing autonomous work on a dedicated branch.

Do not intentionally perform a large autonomous pass directly on the primary branch unless explicitly instructed.

---

# Working Loop

Continue this loop while useful work remains inside the approved scope:

    inspect
        ↓
    identify one concrete improvement
        ↓
    implement
        ↓
    run focused tests
        ↓
    run relevant experiment or demo
        ↓
    inspect the result
        ↓
    document meaningful findings
        ↓
    continue

Do not make one successful edit and immediately stop.

Do not manufacture unnecessary work simply to keep working.

Prefer several small validated improvements over one giant refactor.

---

# Allowed Autonomous Work

You may autonomously:

- fix clear bugs
- improve tests
- improve errors
- improve type hints
- remove obvious duplication
- improve documentation
- create controlled experiments
- research technical questions
- improve deterministic behavior
- improve existing module boundaries when clearly justified
- make small readability refactors
- validate DSP assumptions
- validate physics assumptions
- implement functionality already explicitly requested by the human

You may iterate multiple times.

Testing and experimentation are encouraged.

---

# Restricted Decisions

Do not autonomously:

- redefine Sound Springs
- change the project's scientific objective
- replace the FFT-based approach without explicit approval
- introduce machine learning
- introduce microphone or live-audio systems
- introduce streaming infrastructure
- introduce distributed infrastructure
- introduce databases
- introduce web APIs
- introduce cloud infrastructure
- introduce major concurrency systems
- create generic plugin architectures
- rewrite the project into a different architectural paradigm
- replace functioning subsystems merely because you prefer another design

When a restricted question becomes relevant:

1. research it if useful
2. document what you learned
3. explain the available choices
4. leave the final decision for the humans

---

# Research

Research is encouraged when it supports a concrete engineering question.

Examples:

- WAV / FLAC decoding behavior
- PCM scaling
- stereo handling
- FFT normalization
- frequency resolution
- Hann-window behavior
- spectral leakage
- frame / hop sizing
- numerical integration
- spring stability

Prefer authoritative references.

Research should feed implementation or documentation.

Do not turn an autonomous pass into an unrelated literature survey.

---

# DSP and Physics Changes

For substantial DSP changes, also follow:

    docs/skills/dsp-change.md

For meaningful architectural changes, also follow:

    docs/skills/architecture-change.md

---

# Testing Discipline

Establish a passing baseline before major work.

After each meaningful unit of work:

1. run focused tests
2. fix failures
3. periodically run the complete test suite
4. run important experiments or demos when relevant

Do not perform a massive refactor and wait until the end to discover that behavior broke.

---

# Git Discipline

Prefer working on a dedicated branch.

Keep modifications understandable.

Do not churn files merely for aesthetics.

Do not mix large unrelated changes together.

If commits are requested or appropriate, logical checkpoints are preferred.

Before completing the pass:

    git status

should be understood.

Do not leave mysterious half-finished files without documenting them.

---

# Usage-Limit Shutdown

If the environment exposes remaining session or usage allowance, preserve enough capacity to leave the repository in a coherent state.

When approximately 10% of the relevant available allowance remains:

1. stop beginning new work
2. finish the current small safe change OR revert it
3. run the most important tests
4. restore a coherent repository state
5. update documentation for completed changes
6. update `docs/session-handoff.md`
7. prepare the final engineering report
8. stop

Do not spend the final allowance on:

- cosmetic cleanup
- optional renames
- speculative research
- new experiments
- additional features

If exact usage information is not available, do not invent a percentage.

If the client warns that a limit is approaching, immediately begin the graceful shutdown procedure.

---

# Session Handoff

Before ending a substantial autonomous pass, update:

    docs/session-handoff.md

Keep it concise.

Include:

    Branch:
    Current state:
    Completed work:
    Tests:
    Experiments:
    Research findings:
    Known issues:
    Open human decisions:
    Incomplete work:
    Recommended next task:
    Important files:
    Useful commands:

Replace stale information from previous sessions rather than accumulating an endless journal.

The handoff should reflect the repository's current state.

---

# Completion Standard

The pass is successful when the repository is:

- functioning
- tested
- understandable
- scientifically better validated
- better documented
- easier for a human to continue

A human returning to the repository should not need to reverse-engineer what the agent did.

When useful work inside the approved scope is exhausted, stop.

Do not invent new scope.