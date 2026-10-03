# Architecture

Sound Springs keeps one causal path understandable:

```text
music file
    ↓ acquisition
decoded PCM
    ↓ measurement
spectral amplitudes
    ↓ interpretation
spring forces
    ↓ behavior
simulation state
    ↓ presentation
diagnostic or interactive rendering
```

These are small module boundaries for current requirements, not framework layers for hypothetical inputs or renderers.

## Audio acquisition: `audio.py`

`load_audio_file(path)` accepts `.wav` and `.flac` files and returns an `AudioBuffer`. `python-soundfile` and libsndfile perform decoding. The boundary is independent of the source format:

```python
AudioBuffer(
    samples=<float64 array shaped (frames, channels)>,
    sample_rate=<positive integer>,
)
```

The buffer owns a read-only copy of finite, real-valued samples. Mono still has an explicit one-channel dimension. This prevents format-specific behavior from leaking into DSP and prevents caller mutation from changing a repeated analysis.

All channels are preserved. The current command-line application automatically uses channel 0 only for mono input; multichannel input requires `--channel`. This is deliberate: channel selection is enough to exercise real files without silently deciding whether Sound Springs should average, separately analyze, or otherwise interpret stereo.

## Measurement: `spectrum.py`

`frame_signal` remains a convenient, explicit framing function for tests and small controlled experiments. It returns complete overlapping frames and drops the incomplete tail.

The application pipeline does not materialize that full overlapping matrix. `pipeline.run_pipeline` takes equivalent source slices one at a time, avoiding several copies of a normal-length song when frames overlap.

`analyze_frame`:

1. validates one finite numerical frame;
2. applies a symmetric Hann window;
3. computes NumPy's real FFT;
4. divides magnitudes by the Hann window sum (coherent gain);
5. doubles bins whose negative-frequency mirrors were omitted.

It returns frequencies and one-sided amplitudes. DC and the even-length Nyquist bin are not doubled. For a sinusoid centered exactly on an FFT bin, the measured peak approximates its input amplitude. Off-bin tones still spread across bins because finite framing and windowing impose normal spectral leakage.

Analysis knows nothing about springs, forces, or Matplotlib.

## Interpretation: `mapping.py`

`peak_normalized_forces` converts a non-negative measurement sequence into proportional forces whose peak is `1.0` by default. A sequence of zeros maps to zero force.

This is explicitly a chosen model:

```text
measured target-bin amplitude / largest measured target-bin amplitude
    = applied force fraction
```

It is not part of the FFT and is not a physical law relating sound to springs.

## Behavior: `spring.py`

`Spring` contains the state and parameters of a one-dimensional damped spring. It advances

```text
m*x'' + c*x' + k(x - x0) = F
```

with semi-implicit Euler integration. Physical parameters, force, and timestep must be finite; mass and timestep must be positive; stiffness and damping must be non-negative. `mechanical_energy` exposes kinetic plus spring potential energy for validation.

`timeline.py` gives every complete frame a stable zero-based index, source range `[start_sample, end_sample)`, center sample coordinate, and center timestamp. The center sample is `start + (N - 1) / 2`, the midpoint of the first and last sample positions. Deterministic lookup by playback sample or time selects the nearest frame center, chooses the earlier frame on an exact tie, and selects the nearest end frame for valid source positions outside the analyzed centers.

`pipeline.py` orchestrates the current vertical slice. `AnalysisSettings` records the frame length, hop length, and target frequency. `PipelineResult` contains the immutable `AnalysisTimeline` plus read-only frequencies, amplitudes, forces, and positions. `measurement_at_time` returns a target-bin measurement together with its exact frame identity; it does not mix mapped force or simulation state into the measurement record.

The pipeline does not decode files and does not render.

## Runtime observation: `diagnostics.py`, `benchmark.py`, and `interactive.py`

DiagnosticRun is one scalar record and two output serializers, not a logging or
telemetry framework. The single-file benchmark owns file metadata, process
memory snapshots, and final CSV/TXT output. The pipeline can optionally report
elapsed time for timeline construction, frame analysis, and mapping/simulation
into that record; it never knows where or whether the record is written. DSP
functions remain unaware of diagnostics.

This keeps the normal causal path unchanged while making a complete preparation
run observable:

    decode and pipeline phase measurements
        → one DiagnosticRun
        → one CSV row + one TXT summary

The interactive command adds render-loop scalars to the same record. The CSV
schema, phase boundaries, RSS semantics, first real-WAV baseline, and
limitations are documented in [Runtime diagnostics](diagnostics.md).

## Interactive runtime: `playback.py`, `runtime.py`, and `interactive.py`

`playback.py` owns audio output and the authoritative playback position.
`AudioOutputSettings` makes source rate, output channel count, and a
power-of-two mixer buffer explicit. `initialize_audio_output` requests the
source sample rate, signed 16-bit output, mono/stereo channel count, no silent
format changes, and returns the negotiated SDL driver/format for diagnostics.
The 4,096-sample default is 92.9 ms at 44.1 kHz; it replaces the original
hard-coded 512-sample/11.6 ms request, which was unnecessarily fragile for the
WSLg PulseAudio/RDP boundary.

`MusicPlayback` wraps pygame-ce's single streamed music channel. It starts at
the beginning and exposes SDL_mixer's elapsed playback milliseconds as the
source position. The original WAV is streamed directly by SDL_mixer; the
float64 array decoded for analysis never enters or modifies the playback path.
The module owns no PCM analysis and performs no DSP. Pause/resume is supported.
Seeking is deliberately absent because SDL_mixer does not consistently support
positioning WAV streams and `get_pos()` does not include a start offset.

`runtime.PlaybackSynchronizedSpring` keeps four clocks distinct:

```text
audio playback position
    ↓ nearest deterministic lookup
analysis frame center and precomputed force
    ↓ one update per newly reached analysis frame
fixed simulation timestep = hop length / sample rate
    ↓ independent presentation
render loop capped near 60 FPS
```

If rendering skips analysis frames, the runtime applies every intervening force
once. If a future playback clock moves backward, it resets and replays forces
from the initial spring state. At any selected frame its position therefore
matches the pipeline's deterministic precomputed spring position. Rendering
the same selected frame again does not advance simulation again.

`interactive.py` remains the window, input, and presentation boundary:
decode, resolve one explicit analysis channel, precompute the existing
pipeline, initialize the display, ask `playback.py` to initialize audio,
start playback, read its clock, synchronize the spring, draw, collect scalar
runtime evidence, and close pygame resources. No FFT runs in the interactive
loop.

The presentation now exposes only existing state: equilibrium, current
displacement, a coil, mapped audio-force direction/magnitude, velocity
direction/magnitude, and a short displacement history. Detailed runtime values
toggle with D. This helps explain one spring's motion without adding another
measurement, force, spring, coupling rule, or musical interpretation.

## Presentation: `render.py` and `demo.py`

`create_diagnostic_figure` receives a signal and an already-calculated `PipelineResult`. It plots:

- the waveform samples of the same representative frame;
- one representative amplitude spectrum labeled with its frame index, exact sample range, and center time;
- the simulated spring position over time.

It performs no FFT, feature mapping, or simulation.

Measurement center times and simulation-state times are deliberately separate. A measured frame is located at its center; spring position `i` is the state after force `i` advances the integrator by one hop duration, so its time is `(i + 1) * hop_length / sample_rate` rather than zero.

`demo.py` is the thin application boundary: parse options, load a file, resolve an explicit channel, run the pipeline, print measured facts, and ask the renderer for a figure. It can show or save that figure.

## Deterministic contract

Within one numerical environment, the same selected PCM channel, sample rate, settings, mapping, spring parameters, and initial state produce the same frame identities and numerical series. Tests compare repeated amplitudes, forces, and positions exactly. Cross-platform mathematical checks use documented floating-point tolerances; decoded PCM uses a bit-depth-derived absolute tolerance. Cross-platform pixel identity is not a contract because rendering is downstream of the deterministic values.

## Current limitations

- The entire decoded PCM file is held in memory, although overlapping analysis frames are not duplicated.
- Only one explicitly selected channel and one target frequency are analyzed by the application.
- Peak normalization depends on the largest measurement in the complete file and is not suitable for live input (which is outside current scope).
- The spring integrator has no automatic timestep/stiffness stability guard.
- The pygame view is an intentionally primitive runtime substrate, not a decision about the eventual Sound Springs visual language.
- SDL_mixer reports elapsed playback milliseconds rather than an exact audio-device sample cursor; the first pass has no WAV seek control.
- Pygame exposes the SDL driver and negotiated format but no underrun counter. Under WSLg, the PulseAudio monitor is upstream of the RDP audio transport, so a clean monitor capture cannot prove that the Windows-side output is clean.

These are current boundaries, not invitations to add streaming, live capture, plugin infrastructure, or a new physical model without human direction.
