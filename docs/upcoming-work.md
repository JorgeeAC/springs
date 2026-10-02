# Sound Springs — Upcoming Work

This document tracks upcoming engineering, scientific, and experimental work for Sound Springs.

This is intentionally lightweight.

For now, this file is our shared work board rather than maintaining a large external issue tracker.

Stable task IDs use:

    SS-XXX

Tasks may eventually move into GitHub Issues if coordination becomes complicated.

---

# Status Legend

    [ ] Not started
    [~] In progress
    [x] Complete
    [?] Human decision required
    [-] Parked

Priority:

    P0 — required for correctness / immediate work
    P1 — important next step
    P2 — valuable but not blocking
    P3 — experiment / future idea

---

# Current Direction

The current major project phases are:

    PHASE 1
    Validate the science

        ↓

    PHASE 2
    Establish a reliable analysis timeline

        ↓

    PHASE 3
    Build interactive 60 FPS playback

        ↓

    PHASE 4
    Experiment with actual Sound Springs visual systems

We should resist skipping Phase 1 just because Phase 3 is more fun.

Current milestone state: the scoped Phase 1 contracts and lightweight Phase 2
timeline are complete. The album benchmark validates the current precompute
path well enough to begin Phase 3; playback and interactive rendering are next.

---

# Scientific Validation

## SS-001 — Define Determinism Contract

Priority: P0

Status:

    [x]

Define exactly what deterministic means for each layer.

Document expectations for:

- decoded PCM
- framing
- FFT output
- measured features
- feature-to-force mapping
- physical simulation
- rendering

Likely contract:

    identical input
    + identical parameters
    =
    numerically equivalent analysis and simulation

Pixel-perfect rendering is NOT required.

Acceptance criteria:

- documented
- deterministic regression tests exist
- floating-point tolerance policy is defined

---

## SS-002 — Ground-Truth Signal Suite

Priority: P0

Status:

    [x]

Establish reusable synthetic signals for scientific validation.

Required signals:

- 440 Hz sine
- 440 + 880 Hz two-tone signal
- silence
- chirp
- configurable-amplitude sine

Acceptance criteria:

- signals generated deterministically
- tests reuse the same helpers
- signals remain clearly separated from real music-file input

---

## SS-003 — Parseval Energy Validation

Priority: P0

Status:

    [x]

Implement validation based on Parseval's theorem.

See:

    docs/parseval.md

Initial test should use the full FFT for mathematical clarity.

Later validate the production `rfft` representation.

Acceptance criteria:

    time-domain energy
        ≈
    frequency-domain energy

within documented numerical tolerance.

---

## SS-004 — Define Spectrum Magnitude Semantics

Priority: P0

Status:

    [x]

Answer:

> What exactly does the Y-axis of our spectrum mean?

The original raw FFT magnitude depended on:

- frame length
- Hann-window coherent gain
- FFT normalization
- one-sided versus two-sided spectrum

Research and document:

- current calculation
- units / lack of physical units
- normalization behavior
- whether we want raw magnitude, normalized amplitude, power, or dB for different uses

DO NOT silently change production scaling before understanding the consequences.

Implemented result: production values are documented coherent-gain-corrected one-sided amplitudes. Interior bins are doubled; DC and even-length Nyquist are not. Tests cover amplitude scaling, endpoint bins, and multiple frame lengths.

Acceptance criteria:

- documentation clearly defines current values
- tests verify expected amplitude scaling
- graph labels accurately describe what is being shown

---

## SS-005 — WAV Round-Trip Ground Truth

Priority: P0

Status:

    [x]

Generate a known synthetic signal.

Then:

    known signal
        ↓
    write temporary WAV
        ↓
    load using real Sound Springs file decoder
        ↓
    analyze
        ↓
    verify expected frequencies

This validates the actual application ingestion path.

Acceptance criteria:

- no committed binary music fixture required
- temporary WAV generated during test
- known frequency survives round trip
- sample rate is preserved correctly

---

## SS-006 — FLAC Round-Trip Validation

Priority: P1

Status:

    [x]

If FLAC is supported by the selected decoder, repeat the known-signal round-trip test using FLAC.

Acceptance criteria:

- known frequency survives lossless encoding/decoding
- sample rate remains correct
- behavior matches documented expectations

---

## SS-007 — Silence Invariant

Priority: P0

Status:

    [x]

Silence should produce:

- near-zero measured spectrum
- near-zero mapped force
- no unexplained spring excitation

Acceptance criteria:

- test exists
- tolerance documented
- spring remains at or returns to equilibrium

---

## SS-008 — Amplitude Scaling Validation

Priority: P0

Status:

    [x]

Generate otherwise-identical sine waves at:

    0.25 amplitude
    0.50 amplitude
    1.00 amplitude

Verify how:

- FFT magnitude
- power
- total energy
- mapped force

scale with signal amplitude.

This task should inform SS-004.

---

# Existing Music Analysis

## SS-020 — Improve Representative Frame Reporting

Priority: P1

Status:

    [x]

The earlier static visualization displayed an unidentified "representative frame."

Make the selected frame explicit.

Instead of:

    Representative frame

prefer something similar to:

    Spectrum at 72.413 s

or:

    Spectrum — frame 6234 — 72.413 s

Acceptance criteria:

- exact analyzed location is visible
- waveform and spectrum can be correlated intentionally

---

## SS-021 — Explain Initial Silence

Priority: P2

Status:

    [x]

The first 20 ms of some real music files may contain digital silence.

Improve diagnostic visualization so this is not confusing.

Possible options:

- display a later configurable waveform location
- select waveform region corresponding to representative FFT frame
- show first non-silent region

Implemented choice: display the waveform of the exact representative FFT frame. Both diagnostic panels name the same frame index and sample range, avoiding an unrelated silent file prefix without introducing a product visualization decision.

---

# Analysis Timeline

## SS-030 — Formalize Feature Timeline

Priority: P1

Status:

    [x]

Interactive playback will require a deterministic relationship between:

    playback sample position
        ↓
    analysis frame
        ↓
    audio features

Define a lightweight time-indexed representation.

Important values include:

- frame index
- sample start
- sample center
- sample rate
- hop size
- measured values

Do not introduce databases or streaming infrastructure.

---

## SS-031 — Lookup Features by Playback Position

Priority: P1

Status:

    [x]

Given:

    current_sample

or:

    playback_time_seconds

determine the appropriate analysis frame.

Conceptually:

    sample_position =
        playback_time * sample_rate

    feature_index =
        sample_position / hop_length

The implemented lookup accepts source sample position or playback time, selects the nearest frame center, chooses the earlier frame on an exact tie, clamps valid source-edge positions to the nearest available complete frame, and rejects positions outside the source duration. Interpolation remains a possible later experiment rather than an implicit current behavior.

Initial implementation can remain simple.

---

# Interactive Playback

## SS-100 — Interactive Renderer Technology Spike

Priority: P1

Status:

    [ ]

Research and prototype a renderer capable of maintaining:

    60 FPS

on normal development hardware.

The final interactive renderer should NOT use Matplotlib.

Candidates may include:

- pygame-ce
- pyglet
- ModernGL
- another lightweight Python graphics system

Evaluation criteria:

- reliable 60 FPS
- low CPU overhead
- easy custom drawing
- straightforward input handling
- ability to draw many moving elements
- minimal framework weight
- compatibility with the existing Python math/simulation core

Do NOT prematurely build a web frontend.

Deliverable:

- small benchmark/prototype
- measured FPS
- recommendation
- documented reasoning

---

## SS-101 — Audio Playback Clock

Priority: P1

Status:

    [ ]

Introduce a small playback component capable of:

- play
- pause
- seek
- current playback position

Playback position should become the synchronization reference for interactive visualization.

Do not perform DSP inside the playback layer.

---

## SS-102 — Precompute Analysis Before Playback

Priority: P1

Status:

    [x]

For normal local music files:

    decode
        ↓
    analyze
        ↓
    store feature timeline in memory
        ↓
    begin playback

Avoid calculating expensive DSP inside the 60 FPS render loop unless later measurements demonstrate that it is needed.

Goal:

    render loop does minimal work

The current file pipeline completes all target-bin measurements, mapping, and simulation before diagnostic rendering and stores the immutable analysis timeline in memory. Future playback work should consume this result rather than repeat FFT work in the render loop.

---

## SS-103 — Stable 60 FPS Render Loop

Priority: P1

Status:

    [ ]

Target:

    60 rendered frames per second

The loop should approximately do:

    read playback position
        ↓
    retrieve current analyzed feature
        ↓
    calculate mapped forces
        ↓
    advance simulation
        ↓
    draw

Profile before optimizing.

Acceptance criteria:

- measured stable frame rate
- no obvious audio playback interruption
- no FFT calculations unnecessarily repeated per render frame

---

## SS-104 — Basic Player UI

Priority: P2

Status:

    [ ]

Create a minimal local music-player interface.

Initial controls:

- play / pause
- timeline
- current time
- duration
- seek
- filename

Visual complexity is not required.

The main visual area belongs to the Sound Springs renderer.

---

## SS-105 — Debug Overlay

Priority: P2

Status:

    [ ]

Optional toggleable diagnostic overlay showing:

- FPS
- playback time
- sample position
- analysis-frame index
- selected feature values
- spring force
- spring position

This is useful while developing visual mappings.

It should be removable/disableable for clean visualization.

---

# Sound Springs Visual Experiments

## SS-200 — Multiple Independent Frequency Springs

Priority: P2

Status:

    [ ]

Move from:

    one measured feature
        ↓
    one spring

toward something like:

    N frequency ranges
        ↓
    N forces
        ↓
    N springs

Keep the first experiment deliberately small.

Suggested:

    8 or 16 bands

Do not jump directly to hundreds of physical objects.

---

## SS-201 — Coupled Spring Network

Priority: P2

Status:

    [ ]

Investigate springs influencing neighboring springs.

Questions include:

- what does physical coupling represent musically?
- should neighboring frequencies be physically connected?
- should coupling strength be constant?
- should harmonic relationships affect coupling?

This requires a human conceptual decision before becoming permanent behavior.

---

## SS-202 — Normal Modes Experiment

Priority: P3

Status:

    [ ]

Investigate the relationship between:

- Fourier modes in sound
- normal modes of a coupled spring system

Potential long-term question:

> Can measured musical frequency structures excite characteristic physical modes of a visible system?

Research and experiment before committing architecture.

---

## SS-203 — Alternate Visual Geometries

Priority: P3

Status:

    [ ]

Possible experiments:

- horizontal frequency line
- circle
- radial structure
- mesh
- harmonic relationships
- spatial stereo representation

These are experiments.

Do not prematurely define the final Sound Springs visual identity.

---

# Performance

## SS-300 — Establish Performance Baseline

Priority: P1

Status:

    [~]

Before aggressively optimizing, measure:

- analysis time
- memory usage
- average render FPS
- worst-frame time
- CPU usage where practical

Test with a normal several-minute music file.

We want the frontend/render loop to remain lightweight.

The decode/precompute portion now has a reusable single-file CSV/TXT runner and
an 11-track, 45:42 album baseline, with each track run in a fresh process.
Analysis was 169.9x-183.3x realtime. Median/max live-state RSS increase was
162.367/272.844 MiB; median/max process peak was 333.535/566.727 MiB; retained
precomputed arrays never exceeded 1.851 MiB. All tracks completed and
post-release RSS was 33.672-45.086 MiB. Render FPS, worst-frame time, and CPU
usage remain open, so SS-300 is intentionally still in progress. See
docs/diagnostics.md. Those renderer-dependent measurements should be collected
with the Phase 3 renderer spike; they do not block starting interactive runtime
work. Current evidence does not justify streaming or another memory redesign.

---

## SS-301 — Render Performance Budget

Priority: P2

Status:

    [ ]

At 60 FPS, one frame has approximately:

    16.67 ms

available.

Create a rough budget for:

- feature lookup
- simulation
- rendering
- UI
- overhead

Avoid optimization without measurements.

---

# Documentation / Collaboration

## SS-400 — Keep Upcoming Work Current

Priority: P1

Status:

    [x]

Jon and other contributors should update this file when completing meaningful work.

Basic convention:

    [ ] planned

    [~] currently being worked

    [x] completed

Use an owner when useful:

    Owner: Jorge

or:

    Owner: Jon

Do not add ownership bureaucracy when nobody needs it.

---

## SS-401 — Promote Work to GitHub Issues When Useful

Priority: P3

Status:

    [-]

If this Markdown board becomes annoying:

- create GitHub Issues using the existing SS identifiers
- optionally use GitHub Projects
- keep this file as the high-level roadmap

Do not migrate merely because formal issue tracking looks more professional.

---

# Immediate Recommended Order

The current recommended sequence is:

    SS-101 Playback clock
        ↓
    SS-100 Renderer spike
        ↓
    SS-300 Finish renderer FPS / frame-time / CPU baseline
        ↓
    SS-103 60 FPS loop
        ↓
    begin real Sound Springs visual experiments

This order is intentionally:

    make the numbers trustworthy

before:

    make the graphics sick
