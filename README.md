# Sound Springs

Sound Springs explores one traceable idea:

> Use real properties of sound to produce a repeatable visual structure whose behavior can be explained.

The applications decode a WAV or FLAC music file, measure the amplitude near a chosen frequency over time, map that measured series to force, and advance a damped spring. The diagnostic command renders plots; the first interactive runtime plays a WAV while its playback position drives the same precomputed measurements and spring.

```text
WAV / FLAC file
    ↓
immutable floating-point PCM (frames × channels)
    ↓
overlapping slices → Hann window → one-sided FFT amplitudes
    ↓
chosen frequency-bin amplitude (measurement)
    ↓
peak normalization (interpretation)
    ↓
damped spring trajectory (behavior)
    ↓
diagnostic figure or primitive interactive view (presentation)
```

Synthetic signals remain controlled scientific tools in the tests. They are no longer the application's input source.

## Current capabilities

- WAV and FLAC decoding through `python-soundfile`/libsndfile
- One stable `AudioBuffer` representation with shape `(frames, channels)`
- Preservation of all decoded channels without an implicit stereo mixdown
- Overlapping, complete analysis frames; an incomplete tail is dropped
- Immutable frame identities with exact sample ranges and center timestamps
- Hann-windowed real FFT with coherent-gain and one-sided amplitude correction
- Explicit target-bin measurement and measurement-to-force mapping
- Deterministic nearest-frame measurement lookup by playback position
- Deterministic semi-implicit Euler simulation of one damped spring
- Pygame-ce WAV playback clock synchronized to nearest analysis frames
- Explicit, diagnostic audio output format and dropout-resistant buffering
- Fixed-hop runtime spring stepping in an approximately 60 FPS local window
- Inspectable one-spring view with equilibrium, coil, force, velocity, and history
- Rendering isolated from decoding, DSP, mapping, and simulation
- Centralized one-run CSV/TXT preparation, memory, and runtime diagnostics
- Controlled tests for decoding, framing, Parseval energy, amplitude scaling, known tones, silence, timeline lookup, determinism, and spring damping

## Install

Sound Springs requires Python 3.11 or newer.

```bash
python -m venv .venv
source .venv/bin/activate
python -m pip install -e '.[dev]'
```

## Run the first interactive pass

For a stereo WAV, select the analysis channel explicitly:

```bash
python -m sound_springs.interactive path/to/song.wav \
  --channel 0 \
  --output-dir _jorge_temp_dir/interactive-run
```

Analysis is completely precomputed before playback. The window then uses the
audio playback position to choose the nearest measured frame and applies every
precomputed force through that frame with the fixed analysis-hop timestep. The
same single spring is shown as a coil with a marked equilibrium, audio-force
arrow, velocity arrow, and recent displacement trail. This changes only the
presentation, not the measurement, mapping, or physics.

Space pauses or resumes, D toggles detailed timing/audio diagnostics, and
Escape, Q, or closing the window exits cleanly. The CSV/TXT pair records
preparation time, render timing, analysis-frame offset, process CPU, negotiated
audio backend/format, and mixer buffer. The default 4,096-sample buffer favors
clean playback over low latency; `--audio-buffer-samples` remains an explicit
power-of-two diagnostic override.

## Analyze a music file

Mono input selects its only channel automatically:

```bash
python -m sound_springs.demo path/to/song.wav
```

For stereo or other multichannel input, choose a zero-based channel explicitly. Sound Springs deliberately does not yet impose a project-wide stereo interpretation:

```bash
python -m sound_springs.demo path/to/song.flac --channel 0
```

The diagnostic defaults to the FFT bin nearest 440 Hz, 2,048-sample frames, and a 512-sample hop. These can be changed explicitly:

```bash
python -m sound_springs.demo path/to/song.wav \
  --frequency 880 \
  --frame-length 2048 \
  --hop-length 512
```

For a non-interactive run or a saved diagnostic:

```bash
python -m sound_springs.demo path/to/song.wav --no-show
python -m sound_springs.demo path/to/song.wav --save diagnostic.png --no-show
```

To benchmark one file through decoding and the precomputed pipeline without
rendering, write one CSV record and one TXT summary:

    python -m sound_springs.benchmark path/to/song.wav --channel 0

The routine artifacts go to the Git-ignored diagnostics/runs/ directory by
default. The reviewed album-level evidence is retained separately under
diagnostics/baselines/. See [Runtime diagnostics](docs/diagnostics.md) for the
schema, artifact policy, and memory semantics.

Run the tests with:

```bash
pytest
```

## Project boundaries

The current target-bin-to-unit-force mapping is intentionally simple. An FFT amplitude is a measurement from the file; using it to push a spring is a Sound Springs model choice. Those responsibilities live in separate modules so the distinction stays inspectable.

This remains an early vertical slice. The pygame view validates the runtime substrate; it does not define a finished visual language. The project still does not define a stereo mixdown policy, broader musical features, coupled springs, seeking for WAV playback, or numerical stability guarantees for arbitrary spring parameters and timesteps.

Read [Architecture](docs/architecture.md), [Audio model](docs/audio-model.md),
[Validation](docs/validation.md), and
[Runtime diagnostics](docs/diagnostics.md) for the implemented boundaries,
mathematics, and measurement methodology.
