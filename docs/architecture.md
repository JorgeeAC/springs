# Architecture

Sound Springs is organized around a sequence of distinct responsibilities:

```text
audio input
    ↓
decoded PCM
    ↓
analysis
    ↓
feature mapping
    ↓
simulation
    ↓
rendering
```

This is the target data flow, not a claim that every stage is already a separate component. The current project is one small vertical slice through it.

## Boundaries

### Audio input is not analysis

An input layer obtains audio and decodes it into a common numerical form: samples plus a sample rate. Downstream DSP should operate on those values without caring whether they originally came from WAV, FLAC, or another supported format.

The current code does not decode files. `signal.generate_sine` creates a one-dimensional NumPy array containing a known 440 Hz test signal, while the sample rate is passed separately. This is useful for verifying the math, but it is not the production input model.

### Analysis is not interpretation

Analysis measures properties present in the audio. In the current code, `spectrum.frame_signal` divides a one-dimensional signal into complete, overlapping frames. `spectrum.analyze_frame` applies a Hann window and uses NumPy's real FFT to return non-negative frequency-bin locations and their magnitudes.

A magnitude near 440 Hz means the frame contains strong energy near that frequency. It does not inherently mean “push a spring.” Analysis should remain unaware of springs, forces, and rendering so its measurements can be tested independently and reused with future models.

### Interpretation is not simulation

Feature mapping assigns a meaning to an audio measurement. It is a model chosen by Sound Springs, not another fact discovered in the signal.

The current mapping lives directly in `demo.py`: for every frame, it selects the magnitude at the FFT bin nearest 440 Hz, then divides all selected magnitudes by their maximum. The resulting values are used as scalar forces. This gives the known tone a simple, bounded input while preserving variation across frames. It is intentionally narrow: there is not yet a general feature representation or mapping abstraction.

The simulation receives force and advances its own state. `spring.Spring` contains position, velocity, mass, stiffness, damping, and rest position, and integrates a one-dimensional damped spring with a semi-implicit Euler step. It does not perform audio analysis.

### Simulation is not rendering

Rendering presents results that have already been calculated. The current `demo.py` uses Matplotlib to plot the first 20 milliseconds of the generated waveform, the spectrum of a representative frame, and spring position over time. These plots are diagnostic evidence that the vertical slice behaves sensibly. Matplotlib does not decode audio, calculate spectra, or advance the spring.

Keeping the renderer downstream means an interactive renderer can later replace this static diagnostic view without rewriting the DSP or physical model.

## Implemented now

- Generation of a deterministic sine-wave test signal
- Overlapping, complete frames; incomplete trailing samples are dropped
- A Hann window followed by `numpy.fft.rfft`
- Frequency-bin and unnormalized magnitude output
- Selection and peak normalization of the bin nearest 440 Hz
- A one-dimensional damped spring driven once per analysis hop
- Diagnostic plots and focused tests for spectrum, framing, and spring behavior

These pieces are small functions rather than a larger framework. There is no decoded-audio container, streaming engine, general feature layer, spring network, or renderer interface yet.

## Direction

The next useful progression is to keep validating analysis with signals whose answers are known, then introduce real audio-file decoding into a common PCM representation. Real music can then pass through the same frame-based analysis while the project develops more useful time-varying measurements and explicit mappings.

Analysis, mapping, simulation, and rendering should become separate at the points where real requirements demand it. The visualization can then become interactive, and the physical model can grow from one spring into coupled structures, without changing how files become PCM or how measurements are calculated.

These boundaries keep correctness local and behavior traceable:

```text
visible motion
    ← simulation state
    ← defined force mapping
    ← measured audio feature
    ← decoded samples
```

They also let the project grow through working vertical slices rather than infrastructure for inputs, models, or deployment modes it does not yet support.
