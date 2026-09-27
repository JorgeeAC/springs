# Parseval's Theorem

Parseval's theorem gives Sound Springs an important mathematical sanity check for Fourier analysis.

It helps answer:

> Did our frequency-domain representation preserve the energy contained in the time-domain signal?

This does NOT prove that every decision in our DSP pipeline is correct.

It DOES give us a strong invariant that the Fourier transform itself is behaving consistently with the signal we supplied.

---

# Why We Care

Sound Springs currently performs roughly:

    PCM samples
        ↓
    frame
        ↓
    Hann window
        ↓
    FFT
        ↓
    frequency magnitudes

The FFT can easily feel like a black box:

    numbers go in
        ↓
    np.fft.rfft(...)
        ↓
    completely different-looking numbers come out

Parseval gives us a relationship between those two representations.

The signal may look completely different in the time domain and frequency domain, but its total energy should still agree once the FFT's normalization is accounted for.

---

# Time-Domain Energy

Given a discrete signal:

    x[0], x[1], x[2], ..., x[N-1]

we can define its energy as:

    E_time = sum(|x[n]|²)

In Python:

    energy_time = np.sum(np.abs(signal) ** 2)

A larger-amplitude signal contains more energy.

For example, compare two otherwise identical sine waves:

    amplitude = 0.5

and:

    amplitude = 1.0

Because energy depends on amplitude squared, doubling the amplitude should produce approximately four times the energy.

---

# Frequency-Domain Energy

The Discrete Fourier Transform produces:

    X[k]

for each frequency bin `k`.

With NumPy's default FFT normalization:

    X[k] = sum(x[n] * exp(-i * 2πkn/N))

Parseval's theorem becomes:

    sum(|x[n]|²)
        =
    (1 / N) * sum(|X[k]|²)

Therefore:

    E_time = E_frequency

when the frequency-domain result is normalized appropriately.

In Python using the full FFT:

    spectrum = np.fft.fft(signal)

    energy_time = np.sum(np.abs(signal) ** 2)

    energy_frequency = (
        np.sum(np.abs(spectrum) ** 2)
        / len(signal)
    )

Those two values should be extremely close within floating-point tolerance.

---

# Why This Is Useful

Imagine our FFT implementation produced a spectrum that looked believable:

    strong peak near 440 Hz

That is useful, but appearance alone does not prove much.

Parseval lets us perform another independent check:

    time-domain energy
        ≈
    frequency-domain energy

If they disagree significantly, something about our calculation or normalization needs investigation.

---

# Important: Sound Springs Uses a Hann Window

Our analysis does not normally FFT the untouched frame.

We first apply a Hann window:

    windowed = frame * hann_window

and then calculate:

    FFT(windowed)

Parseval therefore applies to the WINDOWED FRAME.

Correct comparison:

    windowed frame
        ↕
    FFT of windowed frame

Incorrect comparison:

    original unwindowed frame
        ↕
    FFT of windowed frame

The window changes the signal's energy.

That is expected.

---

# Important: rfft Requires Extra Care

Sound Springs currently uses a real FFT:

    np.fft.rfft(...)

Because our input audio is real-valued, the negative-frequency half of the full Fourier spectrum contains redundant information.

`rfft` removes that redundant half.

That is useful for analysis, but it means we cannot simply calculate:

    sum(abs(rfft_result) ** 2) / N

and expect Parseval to work directly.

The missing mirrored frequencies must be accounted for.

For an even-length signal:

- DC (`0 Hz`) appears once
- the Nyquist frequency appears once
- all bins between them represent matching positive and negative frequencies

Those interior bins therefore contribute twice when reconstructing total frequency-domain energy.

Conceptually:

    energy_frequency =
        DC energy
        + Nyquist energy
        + 2 * interior-bin energy

all divided by the appropriate FFT normalization.

---

# Recommended First Implementation

Do NOT modify production DSP simply to make Parseval testing easier.

Instead, create a validation test using:

    np.fft.fft(...)

on the exact same windowed frame.

This keeps the first test extremely easy to reason about:

    windowed = frame * np.hanning(len(frame))

    spectrum = np.fft.fft(windowed)

    energy_time = np.sum(np.abs(windowed) ** 2)

    energy_frequency = (
        np.sum(np.abs(spectrum) ** 2)
        / len(windowed)
    )

    assert_allclose(
        energy_time,
        energy_frequency,
        ...
    )

Once that invariant is understood, we can add a second test validating the one-sided `rfft` representation.

---

# Proposed Tests

## SS Parseval Test 1 — Known Sine

Generate:

    440 Hz sine
    amplitude = 1.0

Apply the same Hann window used by production analysis.

Verify:

    E_time ≈ E_frequency

using the full FFT.

---

## SS Parseval Test 2 — Different Amplitudes

Generate identical sine waves with:

    amplitude = 0.25
    amplitude = 0.50
    amplitude = 1.00

Verify:

    Parseval holds for each signal

and also verify that measured energy scales approximately with amplitude squared.

Expected relative energies:

    0.25² = 0.0625

    0.50² = 0.25

    1.00² = 1.00

This gives us another useful signal-processing sanity check.

---

## SS Parseval Test 3 — Two Tones

Generate:

    440 Hz + 880 Hz

Verify:

    E_time ≈ E_frequency

This demonstrates that Parseval is not specific to a single sine wave.

---

## SS Parseval Test 4 — Arbitrary Deterministic Signal

Create a deterministic pseudo-random signal using an explicit random seed.

Verify:

    E_time ≈ E_frequency

This prevents us from accidentally writing a test that only works because sine waves are unusually simple.

---

## SS Parseval Test 5 — Production rfft

Once the full-FFT implementation is understood, implement the corresponding energy calculation for:

    np.fft.rfft(...)

Correctly account for the omitted negative-frequency bins.

Verify that:

    time-domain energy
        ≈
    reconstructed rfft energy

This directly validates the representation used by production analysis.

---

# What Parseval Does NOT Prove

Passing Parseval does not prove:

- our frame length is ideal
- our hop length is ideal
- the Hann window is the best window
- our FFT magnitude scaling is human-readable
- our frequency-to-force mapping is meaningful
- our spring parameters are good
- our visualization is scientifically unique
- our musical interpretation is correct

It only verifies a very important statement:

> The Fourier representation contains the same total signal energy as the time representation, under the chosen mathematical normalization.

That is still extremely valuable.

---

# Relationship to Determinism

Parseval and determinism solve different problems.

Determinism asks:

> If we analyze the same signal twice, do we obtain the same result?

Parseval asks:

> Is there a mathematical invariant connecting our input signal and its Fourier representation?

We want both.

    correctness / validation
            +
        determinism
            =
    trustworthy foundation

---

# Integration Plan

Sound Springs should eventually maintain multiple layers of validation.

## Signal Ground Truth

Known synthetic inputs:

    440 Hz
    440 + 880 Hz
    silence
    chirp

answer:

> Does the analysis detect what we intentionally put into the signal?

## Parseval

Answers:

> Does energy agree between the time and frequency representations?

## Determinism

Answers:

> Does identical input produce identical analysis output?

## File Round Trip

Generate known signal:

    synthetic signal
        ↓
    write WAV
        ↓
    decode through real application loader
        ↓
    analyze
        ↓
    recover expected properties

Answers:

> Does the real file-ingestion path preserve the signal well enough for our analysis?

Together these form a much stronger validation system than simply looking at a graph and deciding that it looks believable.

---

# Current Status

Parseval validation is planned but should be considered part of the scientific validation work before Sound Springs begins relying heavily on more complex visual mappings.

The first implementation should remain small and transparent.