# Validation

Sound Springs uses controlled signals and generated audio files to validate scientific and engineering contracts. Synthetic inputs answer questions whose expected results are known; they are not application sources.

## Controlled DSP experiments

| Input | Expected result | Current result | Automated coverage |
|---|---|---|---|
| 440 Hz sine, 44,100 Hz sample rate, 2,048 samples | Strongest bin within one bin spacing (21.53 Hz) of 440 Hz | Strongest bin is 430.66 Hz | `test_strongest_frequency_is_near_generated_frequency` |
| 0.4-amplitude, bin-centered 1,000 Hz sine | One-sided amplitude near 0.4 | `0.4` within `2e-6` relative tolerance | `test_bin_centered_sine_reports_its_amplitude` |
| Bin-centered 440 Hz at amplitude 0.6 plus 880 Hz at amplitude 0.2 | Both bins recover their input amplitudes | `0.6` and `0.2` within `2e-6` relative tolerance | `test_two_tone_signal_has_both_expected_amplitudes` |
| Silence | Zero spectral amplitude, zero mapped force, no spring motion | Exactly zero at every stage | spectrum and pipeline silence tests |
| Repeated identical analysis | Identical measurement, force, and position arrays | Exact array equality | spectrum and pipeline repeatability tests |
| Linear chirp from 256 to 1,536 Hz | Dominant per-frame frequency rises over time | Every complete frame's dominant bin increases; first and last are within one bin of their frame-center frequencies | `test_linear_chirp_moves_dominant_frequency_upward` |
| Displaced spring with no forcing | Damping removes mechanical energy | Damped energy is below 5% of undamped energy after the controlled run | `test_damping_removes_mechanical_energy` |

The bin-centered tests use an 8,192 Hz sample rate and 1,024-sample frames, giving exactly 8 Hz per bin. Their frequencies therefore isolate amplitude scaling from leakage caused by an off-bin tone. The chirp uses non-overlapping 512-sample frames and verifies time-varying tracking independently of target-to-force interpretation.

## Decoder and end-to-end experiments

Automated tests write known two-channel PCM-16 data as both WAV and FLAC, decode it through the public input boundary, and verify:

- sample rate;
- frame count and duration;
- channel count and channel values;
- the permanent `(frames, channels)` layout;
- PCM values within one 16-bit quantization step;
- useful failures for unsupported, missing, and corrupt files.

The autonomous maturation pass also ran the complete command-line path over a two-second stereo fixture at 8,192 Hz:

- WAV channel 0 contained a 0.6-amplitude 440 Hz sine. The nearest and strongest bin were both exactly 440.00 Hz.
- FLAC channel 1 contained a 0.25-amplitude 880 Hz sine. The nearest and strongest bin were both exactly 880.00 Hz.
- With a 1,024-sample frame and 256-sample hop, each run produced 61 complete analysis frames and a saved headless diagnostic figure.

This checks format decoding, explicit channel selection, incremental framing, DSP, mapping, simulation, and rendering together without treating a synthetic tone as the application input architecture.

## Research that affected implementation

The implementation choices were checked against primary library documentation:

- [python-soundfile `read`](https://python-soundfile.readthedocs.io/en/0.13.1/#soundfile.read) documents `dtype='float64'`, the sample-rate return value, and `always_2d=True`. Sound Springs uses these to enforce one stable decoded shape.
- [libsndfile's API notes](https://github.com/libsndfile/libsndfile/blob/master/docs/api.md#note-1) explain that integer PCM read through floating-point functions is normalized to `[-1, 1]`. Sound Springs does not repeat or guess bit-depth scaling downstream.
- [libsndfile's supported formats](https://libsndfile.github.io/libsndfile/formats.html) includes Microsoft WAV and FLAC. The application intentionally allow-lists only those established project formats even though the decoder library can handle more.
- [NumPy's DFT documentation](https://numpy.org/doc/stable/reference/routines.fft.html) describes the real-input FFT's non-negative-frequency output and frequency conventions. Sound Springs applies the corresponding one-sided factor while leaving DC and Nyquist undoubled.

The coherent-gain correction is verified experimentally rather than accepted from a library default: dividing by the Hann window sum and applying the one-sided factor recovers the known amplitude of bin-centered tones.

## Interpretation limits

The validation supports the measurement claims above. It does not establish that peak-normalized target-bin amplitude is the best musical feature or that scalar force is the final physical interpretation. Those are project choices. Current tests instead ensure the chosen mapping is explicit, proportional, deterministic, and well-defined for silence.
