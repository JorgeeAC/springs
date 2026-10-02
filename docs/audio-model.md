# Audio model

This document describes the numerical path implemented by Sound Springs.

## Decoded samples

A decoded file becomes sample frames plus a sample rate. For frame index `n` at sample rate \(f_s\), time is

\[
t_n = \frac{n}{f_s}.
\]

`AudioBuffer.samples` always has shape `(frames, channels)` and uses `float64`. Integer PCM decoded by libsndfile is normalized to floating point in approximately `[-1, 1]`. Floating-point WAV values are retained as stored and may exceed that interval, so `AudioBuffer` validates finiteness rather than clipping.

WAV and FLAC therefore reach analysis through the same representation. Format, bit depth, and decoder details do not enter the FFT API.

The application analyzes one channel. Mono input is unambiguous; multichannel input requires an explicit zero-based channel. Averaging or independently interpreting stereo channels remains a human design decision.

## Frames and hop length

Frequency content changes through a song, so Sound Springs analyzes short frames instead of one whole-file FFT. With frame length \(N\) and hop length \(H\), frame `i` starts at sample

\[
s_i = iH.
\]

Only frames with all \(N\) samples are included. The incomplete tail is dropped. Defaults are:

- frame length: 2,048 samples (about 46 ms at 44,100 Hz)
- hop length: 512 samples (about 11.6 ms at 44,100 Hz)

Because the hop is smaller than the frame, adjacent frames overlap. The application processes slices incrementally rather than allocating a full overlapping frame matrix.

Each complete frame has an immutable identity:

- zero-based frame index `i`;
- start sample `iH`;
- exclusive end sample `iH + N`;
- center time `(iH + (N - 1) / 2) / sample_rate`.

Using `(N - 1) / 2` locates the midpoint of the actual first and last samples. For an even-length symmetric Hann window, that center lies halfway between two samples. Playback lookup accepts either a source sample position or time in seconds and selects the nearest frame center, with the earlier frame winning an exact tie. Valid positions before the first center or after the last center select the closest available complete frame; positions outside the decoded source duration are rejected.

## Hann window

The DFT treats a finite frame as one period of a repeating signal. A discontinuity between its end and beginning spreads energy across bins. Sound Springs applies NumPy's symmetric Hann window:

\[
w[n] = \frac{1}{2}\left(1 - \cos\left(\frac{2\pi n}{N-1}\right)\right).
\]

Tapering reduces boundary discontinuities but broadens the main lobe. It does not improve the bin spacing.

## DFT, bins, and one-sided amplitude

For a windowed frame, the DFT is

\[
X[k] = \sum_{n=0}^{N-1} x[n]w[n]e^{-i2\pi kn/N}.
\]

The FFT is an efficient way to compute that DFT. Real inputs have mirrored positive and negative frequencies, so `numpy.fft.rfft` retains the non-negative half. Bin `k` represents

\[
f_k = \frac{k f_s}{N},
\]

and adjacent bins are separated by \(f_s/N\). At 44,100 Hz with 2,048 samples, spacing is about 21.53 Hz. A requested 440 Hz target therefore uses the nearest bin, 430.66 Hz.

Raw `abs(rfft(...))` values scale with frame length and window gain. Sound Springs reports a one-sided amplitude estimate instead:

\[
A[k] = \frac{|X[k]|}{\sum_n w[n]}.
\]

Interior bins are then multiplied by two to account for their omitted negative-frequency mirrors. DC is not doubled, and for even frame lengths the Nyquist bin is not doubled. A bin-centered 0.4-amplitude sine is therefore measured at approximately 0.4 regardless of the supported frame length. For off-bin tones, energy is distributed across nearby bins and a single-bin peak can be lower than the sinusoid amplitude.

The analysis currently discards phase.

## Energy and Parseval validation

Spectrum amplitude and signal energy are related but are not the same quantity. For a windowed frame \(x_w[n]\), NumPy's unnormalized transform obeys

\[
\sum_n |x_w[n]|^2 = \frac{1}{N}\sum_k |X[k]|^2.
\]

For `rfft`, DC and the even-length Nyquist bin contribute once while all interior bins contribute twice to account for their omitted negative-frequency partners. `energy_from_rfft` implements that reconstruction for both odd and even frame lengths. Tests compare it to the energy of the exact Hann-windowed production input. This validates energy preservation independently of the coherent-gain amplitude estimate.

Scaling a signal amplitude by \(a\) scales its measured spectrum amplitude by \(a\), spectral power by \(a^2\), and signal energy by \(a^2\). Tests cover amplitudes 0.25, 0.5, and 1.0 on a bin-centered tone.

## Measurement versus interpretation

The target-bin amplitudes are measurements. Converting them into spring forces is a separate rule:

\[
F_i =
\begin{cases}
0, & \max_j A_j = 0 \\
F_{max}\frac{A_i}{\max_j A_j}, & \text{otherwise.}
\end{cases}
\]

The current default is \(F_{max}=1\). Silence maps to zero force. This normalization preserves the relative target-bin envelope within one file but removes absolute loudness differences between files. That tradeoff belongs to the model, not the FFT.

## Spring simulation

The spring follows

\[
m\ddot{x} + c\dot{x} + k(x-x_0) = F_{audio},
\]

or

\[
\ddot{x} = \frac{F_{audio} - c\dot{x} - k(x-x_0)}{m}.
\]

Each measured force advances the simulation once with timestep

\[
\Delta t = \frac{H}{f_s}.
\]

Semi-implicit Euler first updates velocity and then position from the new velocity. With no external force, damping should reduce the mechanical energy

\[
E = \frac{1}{2}m\dot{x}^2 + \frac{1}{2}k(x-x_0)^2.
\]

Tests verify that behavior for the current numerical regime. The implementation does not yet promise stability for arbitrary parameter/timestep combinations.

The measurement timestamp and simulation timestamp are not interchangeable. Frame `i` is measured at its center time. Recorded spring position `i` is the state after applying its force for one integration step and therefore occurs at `(i + 1) * hop_length / sample_rate` relative to the simulation start.

## Traceability and determinism

The current rendered motion can be traced as:

```text
selected file channel
→ exact overlapping frame
→ Hann-windowed FFT amplitude at the nearest target bin
→ documented peak normalization
→ applied spring force
→ semi-implicit Euler state
→ plotted position
```

No stage intentionally uses randomness. [Validation](validation.md) records the controlled signals and file round trips used to check these claims.
