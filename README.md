# Sound Springs

Sound Springs is a deliberately small experiment that connects basic audio
analysis to a damped spring simulation:

```text
440 Hz sine wave -> overlapping frames -> Hann window -> FFT
                -> magnitude near 440 Hz -> force -> damped spring
```

The implementation favors visible math and readable functions over reusable
frameworks. It requires Python 3.11 or newer.

## Set up

Create and activate a virtual environment, then install the project and its
test dependency:

```bash
python -m venv .venv
source .venv/bin/activate
python -m pip install -e '.[dev]'
```

Run the demonstration:

```bash
python -m sound_springs.demo
```

The demo prints a few analysis facts and opens a Matplotlib window containing
the waveform, one frame's spectrum, and the resulting spring motion.

Run the tests with:

```bash
pytest
```

