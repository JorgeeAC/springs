# Sound Springs

Sound Springs is an audio visualization project built around one principle:

> Use real properties of sound to produce a repeatable visual structure whose behavior can be explained.

The eventual goal is to continuously analyze audio and use its measured behavior to drive interactive physical visualizations. A visible movement should be traceable back through a defined force mapping to a specific audio measurement—not to unrelated randomness.

```text
audio input
    ↓
decoded PCM samples
    ↓
overlapping frames → Hann window → FFT
    ↓
measured audio features
    ↓
defined mapping → physical simulation → rendering
```

## Current state

The current implementation proves the smallest complete version of that pipeline. It generates a two-second, 440 Hz sine wave; analyzes overlapping frames; finds the magnitude of the FFT bin nearest 440 Hz; normalizes that measurement into a force; and applies the force to a damped spring. A Matplotlib window displays the waveform, a representative spectrum, and the spring response.

The generated tone is a controlled test signal, not the intended input architecture. Because its frequency is known in advance, it provides a check that the analysis reports energy in the expected place. Tests also cover framing and basic spring behavior.

Sound Springs does **not** yet decode WAV, FLAC, or other audio files, extract richer time-varying features, simulate coupled physical structures, or provide an interactive renderer. Those capabilities are the direction of the project, not features of the current code.

## Run it

Sound Springs requires Python 3.11 or newer. Create a virtual environment and install the project with its test dependency:

```bash
python -m venv .venv
source .venv/bin/activate
python -m pip install -e '.[dev]'
```

Run the demonstration:

```bash
python -m sound_springs.demo
```

The command prints several analysis facts and opens the diagnostic Matplotlib figure. Run the tests with:

```bash
pytest
```

## Learn more

- [Architecture](docs/architecture.md) describes the pipeline boundaries, the current implementation, and the near-term direction.
- [Audio model](docs/audio-model.md) explains the samples, framing, Fourier analysis, force mapping, and spring math behind the demonstration.
