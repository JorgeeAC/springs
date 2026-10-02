# Sound Springs

Sound Springs explores one traceable idea:

> Use real properties of sound to produce a repeatable visual structure whose behavior can be explained.

The current application decodes a WAV or FLAC music file, measures the amplitude near a chosen frequency over time, maps that measured series to force, advances a damped spring, and renders diagnostic plots.

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
diagnostic figure (presentation)
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
- Rendering isolated from decoding, DSP, mapping, and simulation
- Centralized one-run CSV/TXT timing and process-memory diagnostics
- Controlled tests for decoding, framing, Parseval energy, amplitude scaling, known tones, silence, timeline lookup, determinism, and spring damping

## Install

Sound Springs requires Python 3.11 or newer.

```bash
python -m venv .venv
source .venv/bin/activate
python -m pip install -e '.[dev]'
```

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

This is still an early vertical slice. It does not yet define a stereo mixdown policy, broader musical features, coupled springs, a production renderer, or numerical stability guarantees for arbitrary spring parameters and timesteps.

Read [Architecture](docs/architecture.md), [Audio model](docs/audio-model.md),
[Validation](docs/validation.md), and
[Runtime diagnostics](docs/diagnostics.md) for the implemented boundaries,
mathematics, and measurement methodology.
