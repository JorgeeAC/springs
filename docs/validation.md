# Validation

Sound Springs uses controlled signals and generated audio files to validate scientific and engineering contracts. Synthetic inputs answer questions whose expected results are known; they are not application sources.

## Controlled DSP experiments

| Input | Expected result | Current result | Automated coverage |
|---|---|---|---|
| 440 Hz sine, 44,100 Hz sample rate, 2,048 samples | Strongest bin within one bin spacing (21.53 Hz) of 440 Hz | Strongest bin is 430.66 Hz | `test_strongest_frequency_is_near_generated_frequency` |
| 0.4-amplitude, bin-centered 1,024 Hz sine in 512-, 1,024-, and 2,048-sample frames | One-sided amplitude remains near 0.4 across frame lengths | `0.4` within `2e-6` relative tolerance | `test_bin_centered_sine_reports_its_amplitude_across_frame_lengths` |
| Bin-centered 440 Hz at amplitude 0.6 plus 880 Hz at amplitude 0.2 | Both bins recover their input amplitudes | `0.6` and `0.2` within `2e-6` relative tolerance | `test_two_tone_signal_has_both_expected_amplitudes` |
| Constant 0.3 signal and 0.4-amplitude Nyquist cosine | DC and even-length Nyquist bins are not doubled | Endpoint bins recover 0.3 and 0.4 | `test_dc_and_nyquist_are_not_incorrectly_doubled` |
| Hann-windowed sine, two tones, and seeded arbitrary signal | Full FFT preserves windowed time-domain energy | Parseval agreement within `1e-12` relative/absolute tolerance | `test_parseval_holds_for_full_fft_of_windowed_frame` |
| Odd- and even-length Hann-windowed frames | Weighted `rfft` energy preserves windowed time-domain energy | Parseval agreement within `1e-12` relative/absolute tolerance | `test_rfft_energy_reconstructs_windowed_time_energy` |
| Bin-centered sine at amplitudes 0.25, 0.5, and 1.0 | Spectrum amplitude scales linearly; spectral power and signal energy scale quadratically | Ratios match `a` and `a²` within documented tolerances | `test_sine_amplitude_scales_spectrum_linearly_and_energy_quadratically` |
| Silence | Zero spectral amplitude, zero mapped force, no spring motion | Exactly zero at every stage | spectrum and pipeline silence tests |
| Repeated identical analysis | Identical measurement, force, and position arrays | Exact array equality | spectrum and pipeline repeatability tests |
| Linear chirp from 256 to 1,536 Hz | Dominant per-frame frequency rises over time | Every complete frame's dominant bin increases; first and last are within one bin of their frame-center frequencies | `test_linear_chirp_moves_dominant_frequency_upward` |
| Exact frame timeline and playback lookup | Frame ranges follow hop arithmetic; lookup uses nearest center and earlier tie | Exact sample identities and deterministic selected indices | timeline and pipeline tests |
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

A second parameterized WAV/FLAC test writes a 0.6-amplitude, bin-centered 440 Hz tone, decodes it through `load_audio_file`, and analyzes the decoded channel. Both formats preserve the 8,192 Hz sample rate, identify 440 Hz as the strongest bin, and recover amplitude within two PCM-16 quantization steps. The test fixture is generated in a temporary directory; no binary audio fixture is committed.

The autonomous maturation pass also ran the complete command-line path over a two-second stereo fixture at 8,192 Hz:

- WAV channel 0 contained a 0.6-amplitude 440 Hz sine. The nearest and strongest bin were both exactly 440.00 Hz.
- FLAC channel 1 contained a 0.25-amplitude 880 Hz sine. The nearest and strongest bin were both exactly 880.00 Hz.
- With a 1,024-sample frame and 256-sample hop, each run produced 61 complete analysis frames and a saved headless diagnostic figure.

This checks format decoding, explicit channel selection, incremental framing, DSP, mapping, simulation, and rendering together without treating a synthetic tone as the application input architecture.

The current pass repeated that command-line experiment with a one-second PCM-16 WAV. It produced 29 complete frames for `N=1024`, `H=256`; selected representative frame 14 at samples `[3584, 4608)` with center time `0.499939 s`; measured 440.00 Hz as the nearest and strongest bin; and saved a valid headless diagnostic figure. The rendered spectrum title displays the same exact frame identity.

## Interactive runtime validation

Unit tests use a fake music stream to verify play, pause/resume, elapsed
position, duration clamping, completion, and cleanup without requiring an audio
device. Audio-output tests verify a positive power-of-two buffer, mono/stereo
output resolution, an exact source-rate/signed-16/channel request, and captured
negotiated backend values. Runtime synchronization tests prove that:

- reaching a selected analysis frame applies every precomputed force through
  that frame exactly once;
- repeated renders of one selected frame do not integrate again;
- skipped render frames catch up through every intervening fixed-hop step;
- a backward clock jump resets and deterministically replays;
- the resulting position matches the pipeline's precomputed spring position.

A three-second real-file integration smoke then exercised decode, precompute,
pygame music loading, playback-clock reads, nearest-frame lookup, fixed-step
spring advancement, drawing, metrics serialization, and shutdown using
`Cobra.wav`. SDL dummy video/audio drivers made the run automatable and kept
artifacts in `_jorge_temp_dir`; they cannot validate audible output or real
display/audio-device scheduling. The measured 62.2 FPS average, 19.286 ms worst
interval, zero intervals over 25 ms, and 3.8% one-core process CPU are
provisional renderer evidence rather than a platform guarantee.

The crackling investigation added Pulse sink captures for independent ffplay,
pygame playback-only, and complete runtimes at 512 and 4,096 samples. The
captures rule out clipping, >=2 ms zero gaps, recurring low-energy 10 ms
dropouts, analysis-sample mutation, and DSP/render starvation before the WSLg
RDP boundary. The revised visible run kept the same deterministic
synchronization at 62.4 FPS average, 16.757 ms worst interval, zero intervals
over 25 ms, and 2.878 ms mean nearest-frame offset.

Presentation tests do not assert pixels. They verify the spring polyline keeps
its exact anchor/bob endpoints and includes alternating coil displacement.
The runtime state now exposes the existing spring rest position; no physical
parameter or update equation changed.

## Runtime diagnostic validation

Focused tests exercise the metrics funnel itself. They verify a stable,
single-row CSV, one companion TXT file, explicit unit-bearing columns, scalar
serialization, empty optional memory fields, and a generated WAV through the
benchmark runner without asserting machine-specific performance. A regression
test runs identical input with diagnostics disabled and enabled and compares
all deterministic frequency, amplitude, force, and spring-position arrays
exactly.

The first real-file run used Getting Killed.wav, a 284.533-second, 44.1 kHz
stereo PCM-16 album track, with the default 2,048-sample frame and 512-sample
hop; channel 0 was analyzed. It produced 24,504 complete frames. Decode took
0.409 s; the pipeline took 1.936 s (147.0x realtime), of which frame DSP used
1.904 s. Retained decoded PCM was 191.466 MiB and retained precomputed arrays
were 1.324 MiB. Process RSS rose from 29.582 MiB before load to 233.980 MiB with
both live, while the process-lifetime high-water mark was 412.836 MiB. Full
metric definitions and limitations are in [Runtime diagnostics](diagnostics.md);
the copied test_audio album is local and ignored by Git.

The complete 11-track album baseline then ran every WAV in a separate process.
Preparation took 1.468 s median / 2.731 s maximum, analysis remained at least
169.9x realtime, retained precomputed arrays stayed between 0.867 and 1.851 MiB,
and live-state / process-lifetime peak RSS reached 272.844 / 566.727 MiB. The
tracked [CSV](../diagnostics/baselines/20261002-getting-killed-album-summary.csv)
and [interpretation](../diagnostics/baselines/20261002-getting-killed-album-summary.txt)
preserve the evidence and its limits without committing repetitive per-track
run artifacts. These results support precomputation and do not currently
justify streaming or chunked analysis.

## Determinism and tolerance contract

For one numerical environment, identical decoded samples and identical explicit parameters must produce exactly identical:

- complete-frame identities and lookup results;
- FFT frequency coordinates and measured amplitudes;
- mapped force values;
- simulated positions.

Tests use exact array equality for repeated execution and exact zeros for silence because these contracts do not require approximate comparisons. Mathematical correctness tests use tolerances chosen for the operation:

- `1e-12` relative and absolute for Parseval energy, where floating-point FFT reductions can vary slightly;
- `2e-6` relative for bin-centered coherent-amplitude recovery, tight enough to detect a normalization error;
- up to one PCM-16 quantization step for general decoded sample values and two steps for tone amplitude after windowing and FFT;
- one FFT-bin spacing for off-bin frequency recovery, because finite frequency resolution—not floating-point error—sets that bound.

Cross-library or cross-platform bit identity is not promised. Numerical equivalence under stated tolerances is. Matplotlib pixel identity is outside the deterministic contract.

## Research that affected implementation

The implementation choices were checked against primary library documentation:

- [python-soundfile `read`](https://python-soundfile.readthedocs.io/en/0.13.1/#soundfile.read) documents `dtype='float64'`, the sample-rate return value, and `always_2d=True`. Sound Springs uses these to enforce one stable decoded shape.
- [libsndfile's API notes](https://github.com/libsndfile/libsndfile/blob/master/docs/api.md#note-1) explain that integer PCM read through floating-point functions is normalized to `[-1, 1]`. Sound Springs does not repeat or guess bit-depth scaling downstream.
- [libsndfile's supported formats](https://libsndfile.github.io/libsndfile/formats.html) includes Microsoft WAV and FLAC. The application intentionally allow-lists only those established project formats even though the decoder library can handle more.
- [NumPy's DFT documentation](https://numpy.org/doc/stable/reference/routines.fft.html) describes the real-input FFT's non-negative-frequency output and frequency conventions. Sound Springs applies the corresponding one-sided factor while leaving DC and Nyquist undoubled.
- [pygame-ce music documentation](https://pyga.me/docs/ref/music.html) defines streamed playback and `get_pos()` as elapsed playback milliseconds, notes that it excludes start offsets, and documents format-dependent positioning. The first WAV runtime therefore starts at zero and does not claim seek support.
- [pygame-ce time documentation](https://pyga.me/docs/ref/time.html) documents `Clock.tick(framerate)` as a low-CPU frame-rate limiter. The runtime measures actual loop-start intervals rather than treating the requested limit as achieved FPS.
- [pygame-ce mixer documentation](https://pyga.me/docs/ref/mixer.html) states that smaller mixer buffers can cause dropouts and larger buffers improve reliability at the cost of latency. The 4,096-sample default is an explicit reliability choice for the observed WSLg path.
- [Microsoft's WSLg architecture](https://github.com/microsoft/wslg#pulseaudio) explains that Linux audio passes from PulseAudio through a WSLg sink plugin and the Weston RDP transport to Windows. The clean `RDPSink.monitor` capture therefore rules out upstream sample corruption but not downstream transport underruns.
- [WSLg issue 1429](https://github.com/microsoft/wslg/issues/1429) independently reports crackling with RDP sink underruns. Applying that report to this machine is an inference supported by the boundary-local capture evidence, not a direct underrun count from pygame.

The coherent-gain correction is verified experimentally rather than accepted from a library default: dividing by the Hann window sum and applying the one-sided factor recovers the known amplitude of bin-centered tones.

## Interpretation limits

The validation supports the measurement claims above. It does not establish that peak-normalized target-bin amplitude is the best musical feature or that scalar force is the final physical interpretation. Those are project choices. Current tests instead ensure the chosen mapping is explicit, proportional, deterministic, and well-defined for silence. A dedicated regression test also records the intentional consequence that peak normalization makes otherwise proportional quiet and loud envelopes produce identical forces; absolute loudness is removed at the interpretation boundary.
