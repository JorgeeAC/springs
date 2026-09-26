# Audio model

This document explains the numerical path used by the current demonstration and the model it is intended to support.

## Samples and sample rate

Decoded digital audio is a sequence of amplitude samples:

```text
x[0], x[1], x[2], ...
```

The **sample rate** says how many samples represent one second. At 44,100 Hz, sample index `n` occurs at time

\[
t_n = \frac{n}{44100}.
\]

Plotting sample amplitude against time gives a waveform. Sound Springs needs that data, but a waveform alone does not clearly describe which frequencies are present or how their strengths change.

The current demo generates samples for a 440 Hz sine wave at 44,100 Hz. Future file decoding should produce the same conceptual input—PCM samples and a sample rate—so the analysis does not depend on the original file format.

## Frames and hop length

A frequency analysis of an entire song would summarize frequencies across the recording while losing much of when they occurred. Instead, the signal is divided into short **frames** and each frame is analyzed separately.

The demo uses:

- frame length: 2,048 samples, about 46 ms at 44,100 Hz
- hop length: 512 samples, about 11.6 ms

The hop length is the distance from the start of one frame to the start of the next. Because 512 is smaller than 2,048, neighboring frames overlap. This produces measurements at regular time steps while giving each FFT enough samples to estimate frequency content. The current framing function includes only complete frames and drops any incomplete tail.

## Hann window

An FFT treats a frame as though it repeats forever. If the frame's end does not join smoothly to its beginning, that artificial discontinuity spreads energy across frequency bins. Before the FFT, the code multiplies the frame by a Hann window:

\[
w[n] = \frac{1}{2}\left(1 - \cos\left(\frac{2\pi n}{N-1}\right)\right).
\]

The window tapers both ends toward zero, reducing the boundary discontinuity. The tradeoff is that energy around a frequency is spread across a somewhat wider main lobe. This behavior is expected; a window is not a way to increase raw frequency resolution.

## DFT and FFT

For a frame of \(N\) windowed samples, the Discrete Fourier Transform (DFT) is

\[
X[k] = \sum_{n=0}^{N-1} x[n]w[n]e^{-i2\pi kn/N}.
\]

In programmer terms, the transform compares the frame with a set of oscillations and returns a complex value for each discrete frequency. The Fast Fourier Transform (FFT) is an efficient algorithm for computing the DFT; it is not a different measurement. Sound Springs uses NumPy's FFT implementation rather than implementing the algorithm itself.

Because the input samples are real-valued, negative-frequency results mirror the positive-frequency results. `numpy.fft.rfft` returns only the non-negative half.

## Frequency bins and magnitude

FFT results occur at discrete **bins**. Bin `k` represents

\[
f_k = \frac{k f_s}{N},
\]

where \(f_s\) is the sample rate. Adjacent bins in the current configuration are separated by

\[
\frac{44100}{2048} \approx 21.53\ \text{Hz}.
\]

Therefore 440 Hz does not land exactly on a bin; the demo chooses the closest bin. Tests accept a strongest frequency within one bin spacing of the generated frequency.

Each FFT value is complex and contains magnitude and phase. The current analysis keeps only

\[
|X[k]|,
\]

the magnitude, which says how strongly that frequency component appears in the windowed frame. The returned values are raw, unnormalized FFT magnitudes: they depend on frame length, signal amplitude, and window gain, so they are not yet calibrated physical units.

## Measurement versus interpretation

This boundary is central to Sound Springs. “There is strong magnitude near 440 Hz” is a measurement derived from the samples. “Use that value to push a spring” is an interpretation chosen by the project.

The current demo makes that choice explicitly:

1. Find the magnitude of the bin nearest 440 Hz in every frame.
2. Divide those values by the largest observed value, making the peak force `1.0`.
3. Supply one resulting force value to the spring per hop.

This mapping is simple and deterministic, but it is not a law saying sound literally behaves like a spring. Future mappings should remain equally explicit so visible behavior can be traced back to a measurement.

## Spring simulation

The spring follows

\[
m\ddot{x} + c\dot{x} + k(x-x_0) = F_{audio},
\]

or, solving for acceleration,

\[
\ddot{x} = \frac{F_{audio} - c\dot{x} - k(x-x_0)}{m}.
\]

Here:

- \(x\) is position and \(x_0\) is the resting position.
- \(m\) is mass: larger values produce less acceleration from the same net force.
- \(k\) is stiffness: it pulls the spring back toward rest.
- \(c\) is damping: it removes motion in proportion to velocity.
- \(F_{audio}\) is the force produced by the chosen feature mapping.

`Spring.update` advances this equation with semi-implicit Euler integration: it updates velocity from acceleration, then position from the new velocity. The demo uses a timestep equal to the hop duration, `hop_length / sample_rate`, so each feature measurement advances the simulation once.

One spring is enough to verify the complete causal path. Richer structures can later introduce coupled motion, resonance, memory, and decay without changing what the FFT measurement itself means.

## Determinism and traceability

Given the same samples, analysis settings, mapping, initial spring state, and simulation parameters, the pipeline has no intentional randomness and produces the same underlying behavior. Floating-point results can vary slightly across numerical-library versions or hardware, so determinism should be understood numerically rather than as guaranteed bit-for-bit identity everywhere.

That repeatability supports the question Sound Springs is designed to answer:

```text
Why did this move?
→ this simulation state changed
→ because this mapped force was applied
→ because this measured frequency magnitude changed
→ in these audio samples at this time
```
