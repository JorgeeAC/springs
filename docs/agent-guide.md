# Sound Springs Agent Guide

Read this before making meaningful changes to Sound Springs.

Sound Springs is both:

1. a software project
2. a learning project for DSP, mathematics, physics, and visualization

Human maintainers own the direction of the project.

Agents should help research, implement, test, experiment, document, and iterate.

Agents should not redefine what the project is.

---

# Core Idea

Sound Springs explores this idea:

> Use real properties of sound to produce a repeatable visual structure whose behavior can be explained.

The goal is not simply:

> Make graphics react to music.

We want to be able to ask:

> Why did this visual element move?

and trace the answer through the system:

    audio samples
        ↓
    measured audio property
        ↓
    mapping rule
        ↓
    physical force
        ↓
    simulation behavior
        ↓
    rendered result

That traceability is central to the project.

---

# Current Scope

Sound Springs currently operates on music files.

Expected input formats are:

- WAV
- FLAC

Other normal music-file formats may be considered later.

The project is NOT currently interested in:

- microphone input
- live audio capture
- system audio capture
- network audio
- browser audio
- Spotify integration
- streaming services
- recording devices

Do not introduce architecture for those use cases.

The current problem is already complex enough using normal music files.

---

# Synthetic Signals

Generated signals are scientific tools.

Examples include:

- sine waves
- multiple combined sine waves
- chirps
- impulses
- silence
- noise

They are useful for:

- learning DSP
- verifying equations
- controlled experiments
- regression testing

They are NOT application audio sources.

A generated 440 Hz sine wave exists because we already know what frequency analysis should find.

Real application input is a music file.

---

# Conceptual Pipeline

The intended system is:

    music file
        ↓
    decode file
        ↓
    PCM samples / AudioBuffer
        ↓
    framing
        ↓
    windowing
        ↓
    FFT / DSP analysis
        ↓
    measured audio features
        ↓
    measurement-to-force mapping
        ↓
    physical simulation
        ↓
    simulation state
        ↓
    renderer

Keep these responsibilities understandable.

They do not need complicated architecture.

---

# Audio Input

The audio-input layer answers:

> How do we turn a music file into PCM samples?

This layer may know about:

- paths
- WAV
- FLAC
- decoding libraries
- sample rates
- channels
- PCM representation

The rest of the program should not care whether the original file was WAV or FLAC.

A simple boundary such as:

    audio = load_audio_file(path)

returning something similar to:

    AudioBuffer(
        samples=...,
        sample_rate=...
    )

is preferred over separate class hierarchies for every file format.

Do not create things like:

- WavConnector
- FlacConnector
- ConnectorFactory
- ConnectorRegistry

unless a concrete requirement eventually proves they are necessary.

---

# Analysis

The analysis layer answers:

> What measurable properties exist in these audio samples?

Current examples include:

- FFT output
- FFT magnitudes
- frequency bins
- spectral information

Analysis is measurement.

Analysis must not render graphics.

Analysis should not import Matplotlib or another renderer.

Important DSP math should remain visible enough that humans learning the project can follow it.

---

# Mapping

The mapping layer answers:

> How do we convert measured sound information into inputs for our physical model?

For example:

    FFT magnitude
        ↓
    scale / transform
        ↓
    spring force

This distinction is extremely important.

An FFT magnitude is measured from the signal.

The conversion:

    force = magnitude * some_scale

is a model chosen by Sound Springs.

That mapping can be:

- deterministic
- useful
- meaningful
- mathematically documented

without being a universal law of nature.

Never blur measurement and interpretation together.

---

# Simulation

The simulation layer answers:

> Given these forces, how does our chosen physical system behave?

The initial physical model is a damped spring.

The important equation is:

    m*x'' + c*x' + k(x - x0) = F_audio

In plain English:

    audio force pushes the object

    spring stiffness pulls it toward rest

    damping removes motion over time

    mass determines how strongly force changes acceleration

The important equations should remain understandable.

Do not hide simple physics behind a large abstraction or physics engine without a demonstrated need.

Simulation must not:

- load music files
- decode audio
- calculate FFTs
- render graphics

---

# Rendering

Rendering answers:

> How should calculated information be displayed?

The current renderer is primarily a learning and diagnostic tool.

It may show:

- waveform
- spectrum
- analyzed values
- spring response
- simulation state

Rendering should consume data that has already been calculated.

It should not perform DSP.

It should not determine what audio features mean.

Future rendering technology could change without requiring the analysis or physics code to change.

Possible future renderers might include:

- interactive desktop graphics
- OpenGL
- Pygame
- offline video
- web rendering

Those are future choices.

Do not build them merely because they might eventually exist.

---

# Determinism

Repeatability is an important project property.

Conceptually:

    same PCM samples
    + same sample rate
    + same frame boundaries
    + same window
    + same FFT settings
    + same mapping
    + same spring parameters
    + same initial state
    + same simulation timestep

should produce:

    same analysis data
    + same numerical simulation trajectory

Pixel-perfect rendering across different computers is not currently the important contract.

The important deterministic outputs are the analysis and simulation values.

---

# Engineering Philosophy

Prefer:

- explicit code
- small modules
- visible mathematics
- simple data structures
- controlled experiments
- useful tests
- good naming
- documentation explaining why
- evidence-driven optimization

Avoid:

- speculative architecture
- dependency-injection frameworks
- plugin registries
- service locators
- event buses
- unnecessary factories
- unnecessary async code
- unnecessary multiprocessing
- databases without a reason
- distributed systems
- architecture designed for hypothetical future users

This is a music/DSP side project.

Do not turn it into enterprise infrastructure.

---

# Working With Existing Code

Before significant changes:

1. read this guide
2. inspect relevant documentation
3. inspect the existing implementation
4. run the existing tests
5. run the demo when practical
6. understand current behavior

Do not rewrite working code merely because another structure looks cleaner.

Refactoring should solve a concrete problem.

Good reasons include:

- incorrect behavior
- duplicated logic
- difficult testing
- unclear mathematical behavior
- violated responsibility boundaries
- approved functionality cannot be added cleanly

"This architecture looks more professional" is not a valid reason.

---

# Research

Research is encouraged.

This project intentionally enters areas that the maintainers are learning.

Useful research topics include:

- PCM representation
- sampling
- FFT behavior
- FFT normalization
- frequency resolution
- window functions
- spectral leakage
- framing
- hop length
- stereo audio
- WAV / FLAC decoding
- numerical integration
- damping
- resonance
- coupled oscillators
- normal modes

Research should answer a concrete implementation or scientific question.

Prefer authoritative sources such as:

- library documentation
- textbooks
- university material
- papers
- established DSP references

If research changes an implementation decision, document:

- what question was investigated
- what was learned
- what decision was made
- why
- whether the decision is provisional

Do not change the project's overall direction simply because another project does something differently.

---

# Controlled Experiments

Controlled experiments are strongly encouraged.

Examples:

## 440 Hz sine

Expected:

A strong spectral peak should appear near 440 Hz within the resolution of the FFT.

## Two-tone signal

Example:

    440 Hz + 880 Hz

Expected:

Strong spectral evidence should exist near both frequencies.

## Silence

Expected:

Near-zero spectral magnitude and no meaningful audio-driven spring force.

## Chirp

Expected:

The dominant detected frequency should move through the spectrum over time.

Experiments exist to help understand and validate behavior.

They are not merely visual demos.

---

# Testing

Tests should focus on real scientific or behavioral contracts.

Examples:

- known frequencies are detected approximately correctly
- framing boundaries are correct
- repeated analysis is deterministic
- silence does not create unexplained spectral energy
- audio decoding preserves expected sample rate
- the spring remains still at equilibrium without force
- damping reduces oscillation
- invalid physical parameters are rejected

Use numerical tolerances where floating-point equality is inappropriate.

Do not test Matplotlib pixels.

---

# Human Decisions

Agents should not silently make conceptual decisions that materially change what Sound Springs means.

Examples:

- should stereo channels be averaged or analyzed independently?
- should frequency bands correspond to musical notes?
- how should phase influence the visualization?
- what should coupling between springs represent?
- should harmonic relationships alter spring connections?
- what geometry should represent musical relationships?

Agents may:

- research the question
- create a small experiment
- describe tradeoffs
- document options

Then leave the final conceptual decision to the human maintainers.

Use `docs/session-handoff.md` when appropriate.

---

# Documentation

Documentation is shared project memory.

Keep documentation aligned with actual code.

Do not document hypothetical systems as though they already exist.

When meaningful behavior changes, update the relevant documentation.

Important architectural or scientific decisions should be recorded rather than living only inside code or chat history.

---

# Agent Skills

Reusable agent procedures live under:

    docs/skills/

Current skills include:

    autonomous-pass.md
    dsp-change.md
    architecture-change.md

Use them when the task matches.

Do not invent new skills for every small task.

---

# Autonomous Work

When explicitly asked to perform a substantial autonomous engineering pass, follow:

    docs/skills/autonomous-pass.md

An autonomous pass should make the repository:

- easier to understand
- better tested
- more scientifically validated
- better documented
- easier for the humans to continue

An autonomous pass should NOT redesign the project while the humans are away.

---

# Session Handoff

Substantial autonomous work should update:

    docs/session-handoff.md

The purpose of this file is to let another human or agent quickly understand where the previous session ended.

It should describe the CURRENT state rather than becoming an endless diary.

---

# Core Invariant

When uncertain, preserve this distinction:

    ACQUISITION
        ↓
    MEASUREMENT
        ↓
    INTERPRETATION
        ↓
    BEHAVIOR
        ↓
    PRESENTATION

For Sound Springs:

    music file
        ↓
    PCM samples
        ↓
    DSP analysis
        ↓
    feature mapping
        ↓
    physics
        ↓
    rendering

These boundaries should remain understandable.

They do not need to become complicated frameworks.# Sound Springs Agent Guide

Read this before making meaningful changes to Sound Springs.

Sound Springs is both:

1. a software project
2. a learning project for DSP, mathematics, physics, and visualization

Human maintainers own the direction of the project.

Agents should help research, implement, test, experiment, document, and iterate.

Agents should not redefine what the project is.

---

# Core Idea

Sound Springs explores this idea:

> Use real properties of sound to produce a repeatable visual structure whose behavior can be explained.

The goal is not simply:

> Make graphics react to music.

We want to be able to ask:

> Why did this visual element move?

and trace the answer through the system:

    audio samples
        ↓
    measured audio property
        ↓
    mapping rule
        ↓
    physical force
        ↓
    simulation behavior
        ↓
    rendered result

That traceability is central to the project.

---

# Current Scope

Sound Springs currently operates on music files.

Expected input formats are:

- WAV
- FLAC

Other normal music-file formats may be considered later.

The project is NOT currently interested in:

- microphone input
- live audio capture
- system audio capture
- network audio
- browser audio
- Spotify integration
- streaming services
- recording devices

Do not introduce architecture for those use cases.

The current problem is already complex enough using normal music files.

---

# Synthetic Signals

Generated signals are scientific tools.

Examples include:

- sine waves
- multiple combined sine waves
- chirps
- impulses
- silence
- noise

They are useful for:

- learning DSP
- verifying equations
- controlled experiments
- regression testing

They are NOT application audio sources.

A generated 440 Hz sine wave exists because we already know what frequency analysis should find.

Real application input is a music file.

---

# Conceptual Pipeline

The intended system is:

    music file
        ↓
    decode file
        ↓
    PCM samples / AudioBuffer
        ↓
    framing
        ↓
    windowing
        ↓
    FFT / DSP analysis
        ↓
    measured audio features
        ↓
    measurement-to-force mapping
        ↓
    physical simulation
        ↓
    simulation state
        ↓
    renderer

Keep these responsibilities understandable.

They do not need complicated architecture.

---

# Audio Input

The audio-input layer answers:

> How do we turn a music file into PCM samples?

This layer may know about:

- paths
- WAV
- FLAC
- decoding libraries
- sample rates
- channels
- PCM representation

The rest of the program should not care whether the original file was WAV or FLAC.

A simple boundary such as:

    audio = load_audio_file(path)

returning something similar to:

    AudioBuffer(
        samples=...,
        sample_rate=...
    )

is preferred over separate class hierarchies for every file format.

Do not create things like:

- WavConnector
- FlacConnector
- ConnectorFactory
- ConnectorRegistry

unless a concrete requirement eventually proves they are necessary.

---

# Analysis

The analysis layer answers:

> What measurable properties exist in these audio samples?

Current examples include:

- FFT output
- FFT magnitudes
- frequency bins
- spectral information

Analysis is measurement.

Analysis must not render graphics.

Analysis should not import Matplotlib or another renderer.

Important DSP math should remain visible enough that humans learning the project can follow it.

---

# Mapping

The mapping layer answers:

> How do we convert measured sound information into inputs for our physical model?

For example:

    FFT magnitude
        ↓
    scale / transform
        ↓
    spring force

This distinction is extremely important.

An FFT magnitude is measured from the signal.

The conversion:

    force = magnitude * some_scale

is a model chosen by Sound Springs.

That mapping can be:

- deterministic
- useful
- meaningful
- mathematically documented

without being a universal law of nature.

Never blur measurement and interpretation together.

---

# Simulation

The simulation layer answers:

> Given these forces, how does our chosen physical system behave?

The initial physical model is a damped spring.

The important equation is:

    m*x'' + c*x' + k(x - x0) = F_audio

In plain English:

    audio force pushes the object

    spring stiffness pulls it toward rest

    damping removes motion over time

    mass determines how strongly force changes acceleration

The important equations should remain understandable.

Do not hide simple physics behind a large abstraction or physics engine without a demonstrated need.

Simulation must not:

- load music files
- decode audio
- calculate FFTs
- render graphics

---

# Rendering

Rendering answers:

> How should calculated information be displayed?

The current renderer is primarily a learning and diagnostic tool.

It may show:

- waveform
- spectrum
- analyzed values
- spring response
- simulation state

Rendering should consume data that has already been calculated.

It should not perform DSP.

It should not determine what audio features mean.

Future rendering technology could change without requiring the analysis or physics code to change.

Possible future renderers might include:

- interactive desktop graphics
- OpenGL
- Pygame
- offline video
- web rendering

Those are future choices.

Do not build them merely because they might eventually exist.

---

# Determinism

Repeatability is an important project property.

Conceptually:

    same PCM samples
    + same sample rate
    + same frame boundaries
    + same window
    + same FFT settings
    + same mapping
    + same spring parameters
    + same initial state
    + same simulation timestep

should produce:

    same analysis data
    + same numerical simulation trajectory

Pixel-perfect rendering across different computers is not currently the important contract.

The important deterministic outputs are the analysis and simulation values.

---

# Engineering Philosophy

Prefer:

- explicit code
- small modules
- visible mathematics
- simple data structures
- controlled experiments
- useful tests
- good naming
- documentation explaining why
- evidence-driven optimization

Avoid:

- speculative architecture
- dependency-injection frameworks
- plugin registries
- service locators
- event buses
- unnecessary factories
- unnecessary async code
- unnecessary multiprocessing
- databases without a reason
- distributed systems
- architecture designed for hypothetical future users

This is a music/DSP side project.

Do not turn it into enterprise infrastructure.

---

# Working With Existing Code

Before significant changes:

1. read this guide
2. inspect relevant documentation
3. inspect the existing implementation
4. run the existing tests
5. run the demo when practical
6. understand current behavior

Do not rewrite working code merely because another structure looks cleaner.

Refactoring should solve a concrete problem.

Good reasons include:

- incorrect behavior
- duplicated logic
- difficult testing
- unclear mathematical behavior
- violated responsibility boundaries
- approved functionality cannot be added cleanly

"This architecture looks more professional" is not a valid reason.

---

# Research

Research is encouraged.

This project intentionally enters areas that the maintainers are learning.

Useful research topics include:

- PCM representation
- sampling
- FFT behavior
- FFT normalization
- frequency resolution
- window functions
- spectral leakage
- framing
- hop length
- stereo audio
- WAV / FLAC decoding
- numerical integration
- damping
- resonance
- coupled oscillators
- normal modes

Research should answer a concrete implementation or scientific question.

Prefer authoritative sources such as:

- library documentation
- textbooks
- university material
- papers
- established DSP references

If research changes an implementation decision, document:

- what question was investigated
- what was learned
- what decision was made
- why
- whether the decision is provisional

Do not change the project's overall direction simply because another project does something differently.

---

# Controlled Experiments

Controlled experiments are strongly encouraged.

Examples:

## 440 Hz sine

Expected:

A strong spectral peak should appear near 440 Hz within the resolution of the FFT.

## Two-tone signal

Example:

    440 Hz + 880 Hz

Expected:

Strong spectral evidence should exist near both frequencies.

## Silence

Expected:

Near-zero spectral magnitude and no meaningful audio-driven spring force.

## Chirp

Expected:

The dominant detected frequency should move through the spectrum over time.

Experiments exist to help understand and validate behavior.

They are not merely visual demos.

---

# Testing

Tests should focus on real scientific or behavioral contracts.

Examples:

- known frequencies are detected approximately correctly
- framing boundaries are correct
- repeated analysis is deterministic
- silence does not create unexplained spectral energy
- audio decoding preserves expected sample rate
- the spring remains still at equilibrium without force
- damping reduces oscillation
- invalid physical parameters are rejected

Use numerical tolerances where floating-point equality is inappropriate.

Do not test Matplotlib pixels.

---

# Human Decisions

Agents should not silently make conceptual decisions that materially change what Sound Springs means.

Examples:

- should stereo channels be averaged or analyzed independently?
- should frequency bands correspond to musical notes?
- how should phase influence the visualization?
- what should coupling between springs represent?
- should harmonic relationships alter spring connections?
- what geometry should represent musical relationships?

Agents may:

- research the question
- create a small experiment
- describe tradeoffs
- document options

Then leave the final conceptual decision to the human maintainers.

Use `docs/session-handoff.md` when appropriate.

---

# Documentation

Documentation is shared project memory.

Keep documentation aligned with actual code.

Do not document hypothetical systems as though they already exist.

When meaningful behavior changes, update the relevant documentation.

Important architectural or scientific decisions should be recorded rather than living only inside code or chat history.

---

# Agent Skills

Reusable agent procedures live under:

    docs/skills/

Current skills include:

    autonomous-pass.md
    dsp-change.md
    architecture-change.md

Use them when the task matches.

Do not invent new skills for every small task.

---

# Autonomous Work

When explicitly asked to perform a substantial autonomous engineering pass, follow:

    docs/skills/autonomous-pass.md

An autonomous pass should make the repository:

- easier to understand
- better tested
- more scientifically validated
- better documented
- easier for the humans to continue

An autonomous pass should NOT redesign the project while the humans are away.

---

# Session Handoff

Substantial autonomous work should update:

    docs/session-handoff.md

The purpose of this file is to let another human or agent quickly understand where the previous session ended.

It should describe the CURRENT state rather than becoming an endless diary.

---

# Core Invariant

When uncertain, preserve this distinction:

    ACQUISITION
        ↓
    MEASUREMENT
        ↓
    INTERPRETATION
        ↓
    BEHAVIOR
        ↓
    PRESENTATION

For Sound Springs:

    music file
        ↓
    PCM samples
        ↓
    DSP analysis
        ↓
    feature mapping
        ↓
    physics
        ↓
    rendering

These boundaries should remain understandable.

They do not need to become complicated frameworks.