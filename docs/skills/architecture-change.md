# Skill: Architecture Change

Use this procedure before making a meaningful architectural change.

Architecture exists to solve current problems.

It is not a goal by itself.

---

# 1. Identify the Problem

Before changing architecture, answer:

> What concrete problem does this change solve?

Good reasons include:

- rendering currently performs DSP
- audio decoding is duplicated
- simulation cannot be tested independently
- responsibilities are mixed
- approved functionality cannot be implemented cleanly

Bad reason:

> This architecture looks more professional.

---

# 2. Preserve the Core Flow

Sound Springs should remain understandable as:

    audio acquisition
        ↓
    measurement
        ↓
    interpretation
        ↓
    physical behavior
        ↓
    presentation

In current project terms:

    music file
        ↓
    decoding
        ↓
    DSP
        ↓
    mapping
        ↓
    simulation
        ↓
    rendering

An architecture change should clarify these responsibilities.

It should not create layers merely because layers are possible.

---

# 3. Avoid Speculative Infrastructure

Do not introduce without demonstrated need:

- dependency injection frameworks
- service locators
- plugin registries
- provider registries
- abstract factories
- event buses
- repository patterns
- distributed systems
- databases
- network services

Prefer the smallest boundary that solves the current problem.

---

# 4. Protect Existing Behavior

Before refactoring:

1. establish the current test baseline
2. understand current behavior
3. add regression coverage if needed

Refactor incrementally.

Run tests during the change rather than only afterward.

Do not silently remove working behavior.

---

# 5. Keep Human Ownership

If an architectural change also determines what Sound Springs should become in the future, that is probably a human decision.

Agents may:

- investigate
- prototype
- document alternatives
- explain tradeoffs

Do not silently choose the future product direction.

Record unresolved decisions in:

    docs/session-handoff.md