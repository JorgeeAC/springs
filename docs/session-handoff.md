# Session Handoff

**Branch:** `agent/maturation-pass-01`

**Current state:** The branch contains a coherent, committed maturation pass. The application now accepts WAV/FLAC files, produces separated numerical pipeline results, and renders them diagnostically. Full tests pass.

**Completed work:**

- Added immutable `(frames, channels)` `AudioBuffer` and WAV/FLAC decoding with actionable errors.
- Preserved channels and required an explicit channel for multichannel application input.
- Changed raw FFT magnitudes to Hann-coherent-gain-corrected one-sided amplitudes.
- Separated measurement-to-force mapping, pipeline orchestration, and rendering.
- Avoided materializing all overlapping frames in the application pipeline.
- Added finite-value validation and mechanical-energy reporting to the spring.
- Expanded decoding, DSP, mapping, pipeline, determinism, channel-policy, and physics tests.
- Updated README, architecture, numerical model, and validation documentation.

**Tests:** `.venv/bin/pytest -q` passes 31 tests. `.venv/bin/python -m compileall -q src tests` passes. Run both again after any subsequent edits.

**Experiments:** A generated 8,192 Hz, two-second stereo fixture was written as PCM-16 WAV and FLAC. WAV channel 0 measured a 440.00 Hz strongest/target bin; FLAC channel 1 measured 880.00 Hz. Each produced 61 frames with `N=1024`, `H=256`, and saved a valid headless diagnostic figure. Controlled tests recover 0.4 for a bin-centered 0.4 sine, recover 0.6 and 0.2 from a two-tone input, track a 256-to-1,536 Hz chirp upward frame by frame, and keep silence exactly at zero through simulation.

**Research findings:** `python-soundfile` can force a stable two-dimensional `(frames, channels)` result; libsndfile normalizes integer PCM when read as floating point; WAV and FLAC are supported. NumPy `rfft` returns the non-negative-frequency half, so one-sided amplitude correction doubles interior bins but not DC/Nyquist. See `docs/validation.md` for primary references.

**Known issues:** The whole decoded file remains in memory. Only one channel and target bin drive one spring. Peak normalization removes absolute loudness differences. Off-bin amplitudes exhibit expected leakage. Semi-implicit Euler has no general stability guard. Diagnostic Matplotlib rendering is not interactive product rendering.

**Open human decisions:** Choose the intended stereo policy (explicit channel, average mixdown, or independent analysis); choose which time-varying musical measurements should supersede the narrow target-bin example; decide what those measurements should mean physically and visually.

**Incomplete work:** No known half-finished implementation. `trinidad-diagnostic.png` is an intentionally untracked local artifact and must not be committed. Temporary validation artifacts under `/tmp/sound-springs-validation.XJdcyE` are not required.

**Recommended next task:** Have a human choose one stereo policy and one musically useful measured feature. Then implement that single feature as a new explicit measurement with controlled fixtures before changing the physical or visual model.

**Important files:** `src/sound_springs/audio.py`, `spectrum.py`, `mapping.py`, `pipeline.py`, `spring.py`, `render.py`, `demo.py`, plus `docs/architecture.md`, `docs/audio-model.md`, and `docs/validation.md`.

**Useful commands:**

```bash
.venv/bin/pytest -q
.venv/bin/python -m compileall -q src tests
MPLBACKEND=Agg MPLCONFIGDIR=/tmp/matplotlib-cache \
  .venv/bin/python -m sound_springs.demo path/to/file.wav --no-show
git diff --check
git status --short --branch
```
