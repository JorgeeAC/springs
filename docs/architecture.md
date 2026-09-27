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
diagnostic rendering
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

`pipeline.py` orchestrates the current vertical slice. `AnalysisSettings` records the frame length, hop length, and target frequency. `PipelineResult` contains read-only frequencies, amplitudes, forces, and positions for deterministic downstream consumption.

The pipeline does not decode files and does not render.

## Presentation: `render.py` and `demo.py`

`create_diagnostic_figure` receives a signal and an already-calculated `PipelineResult`. It plots:

- the first 20 ms of the selected input channel;
- one representative amplitude spectrum;
- the simulated spring position over time.

It performs no FFT, feature mapping, or simulation.

`demo.py` is the thin application boundary: parse options, load a file, resolve an explicit channel, run the pipeline, print measured facts, and ask the renderer for a figure. It can show or save that figure.

## Deterministic contract

Within one numerical environment, the same selected PCM channel, sample rate, settings, mapping, spring parameters, and initial state produce the same numerical series. Tests compare repeated amplitudes, forces, and positions exactly. Cross-platform pixel identity is not a contract; rendering is downstream of the deterministic values.

## Current limitations

- The entire decoded PCM file is held in memory, although overlapping analysis frames are not duplicated.
- Only one explicitly selected channel and one target frequency are analyzed by the application.
- Peak normalization depends on the largest measurement in the complete file and is not suitable for live input (which is outside current scope).
- The spring integrator has no automatic timestep/stiffness stability guard.
- The renderer is a diagnostic Matplotlib view rather than the eventual interactive visualization.

These are current boundaries, not invitations to add streaming, live capture, plugin infrastructure, or a new physical model without human direction.
