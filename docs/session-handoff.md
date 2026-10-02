# Session Handoff

**Branch:** `agent/maturation-pass-01`

**Current state:** The working tree contains a coherent, uncommitted scientific/timeline maturation pass plus the reviewed SS-300 decode/precompute diagnostics baseline. Phase 1 validation and the initial Phase 2 timeline are complete. The current scientific, timeline, and diagnostic foundation is sufficiently validated to begin interactive runtime work; the album evidence does not justify memory or streaming redesign. Full tests pass.

**Completed work:**

- Added full-FFT and production-style `rfft` Parseval energy validation, including odd/even frame lengths and explicit one-sided endpoint handling.
- Added configurable-amplitude sine and silence generators; validated linear spectral-amplitude scaling and quadratic energy scaling at amplitudes 0.25, 0.5, and 1.0.
- Added DC, Nyquist, multiple-frame-length, complex-input rejection, and peak-normalization regression coverage.
- Added true PCM-16 WAV and FLAC tone round trips through decoding and spectral analysis.
- Added immutable `AnalysisTimeline` frame identities: index, start sample, exclusive end sample, and exact center time.
- Added deterministic nearest-center lookup by playback sample or time, an earlier-frame tie rule, and measurement lookup returning the value plus exact frame identity.
- Separated frame-center measurement times from post-integration simulation-state times; corrected the spring diagnostic time axis.
- Made the CLI and diagnostic figure report the exact representative frame. The waveform and spectrum now show the same source frame.
- Added DiagnosticRun as one centralized scalar record with stable one-row CSV and compact TXT serialization.
- Added a single-file benchmark command with decode, complete pipeline, DSP, timeline, mapping/simulation, and total-preparation timing.
- Added Linux process RSS snapshots and process-lifetime peak RSS, exact retained NumPy payload sizes, explicit delta semantics, and release-after-collection observation.
- Added diagnostics structure/serialization tests, a generated-WAV runner test, and exact pipeline-result equality with instrumentation enabled versus disabled.
- Copied the Getting Killed WAV album to the Git-ignored test_audio/Geese_Getting_Killed directory at Jorge's request; no audio is tracked by Git.
- Ran all 11 album WAVs through separate benchmark CLI processes, retained each CSV/TXT pair, and added one album aggregate CSV plus one interpreted TXT summary.
- Froze artifact handling: routine diagnostics/runs output is Git-ignored, while one compact album aggregate CSV/TXT pair is tracked under diagnostics/baselines.
- Updated README, architecture, audio model, Parseval notes, validation evidence, and the work board to reflect current behavior.

**Tests:** `.venv/bin/pytest -q` passes 59 tests. `.venv/bin/python -m compileall -q src tests` and `git diff --check` pass.

**Experiments:** Eleven fresh Python processes analyzed channel 0 of every 44.1 kHz stereo PCM-16 Getting Killed WAV with `N=2048` and `H=512`. Total album duration was 45:42.453. Median/max preparation was 1.468/2.731 s and median/minimum analysis speed was 177.6x/169.9x realtime. The canonical aggregate is tracked under `diagnostics/baselines/`; raw per-track pairs remain local under the ignored `diagnostics/runs/`. Earlier synthetic WAV/FLAC and headless-render experiments remain covered by tests and validation notes.

**Research findings:** Decoded float64 stereo PCM dominated memory and scaled with duration, reaching 268.546 MiB; retained precomputed arrays were only 0.867-1.851 MiB. Median/max live-state RSS increase was 162.367/272.844 MiB and median/max peak was 333.535/566.727 MiB. Three tracks exceeded 400 MiB peak. The peak remains consistent with the decoder array and AudioBuffer's owned copy briefly coexisting, but RSS is not allocation attribution. Post-release RSS was 33.672-45.086 MiB in every independent process. Analysis was consistently far faster than realtime. The album does not justify streaming; it does justify defining a target memory budget.

**Known issues:** The whole decoded file and all channels remain as float64 PCM even though only one channel is analyzed. AudioBuffer ownership creates a useful immutable boundary but appears to cause a large transient decode peak. Current/peak RSS are Linux process-level observations affected by imports, allocators, native code, filesystem cache, and system load. Each album track was sampled only once on one machine and all share one encoding. Only one explicit channel and target bin drive one spring. Peak normalization removes absolute loudness differences. The spring integrator has no general stability guard. Nearest-center lookup does not interpolate. Matplotlib remains a diagnostic renderer.

**Open human decisions:** Choose the intended stereo policy (explicit channel, average mixdown, or independent analysis); choose which time-varying musical measurements should supersede the narrow target-bin example; decide what those measurements should mean physically and visually. No choice was made about frequency grouping, stereo meaning, multiple springs, coupling, phase, or visual geometry.

**Incomplete work:** SS-300 remains in progress only for renderer-dependent FPS, worst-frame time, and CPU measurements. The local `test_audio/` album copy and routine `diagnostics/runs/` output are intentionally Git-ignored. `_jorge_temp_dir/` contains pre-existing untracked diagnostic images owned by Jorge and was left untouched.

**Recommended next task:** Begin Phase 3 with SS-101's playback clock, then use the SS-100 renderer spike to collect SS-300's remaining FPS/frame-time/CPU evidence. Define a target-platform resident and peak memory budget before considering memory work; do not implement streaming unless a real target or longer-file test shows the current approach fails it.

**Important files:** `src/sound_springs/diagnostics.py`, `benchmark.py`, `pipeline.py`, `timeline.py`; `tests/test_diagnostics.py`, `test_pipeline.py`; `docs/diagnostics.md`, `docs/validation.md`, `docs/upcoming-work.md`; `diagnostics/baselines/20261002-getting-killed-album-summary.csv` and `.txt`.

**Useful commands:**

```bash
.venv/bin/pytest -q
.venv/bin/python -m compileall -q src tests
.venv/bin/python -m sound_springs.benchmark \
  'test_audio/Geese_Getting_Killed/Getting Killed.wav' --channel 0
MPLBACKEND=Agg MPLCONFIGDIR=/tmp/matplotlib-cache \
  .venv/bin/python -m sound_springs.demo path/to/file.wav --no-show
git diff --check
git status --short --branch
```
