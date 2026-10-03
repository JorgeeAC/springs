# Session Handoff

**Branch:** `feature/interactive-runtime-01`

**Current state:** The first interactive runtime now has an explicitly configured playback path and an inspectable single-spring renderer. The original WAV is streamed directly at its source rate/channel count while the separate decoded array is used only for precomputed analysis. Playback time still selects the nearest analysis frame and advances the unchanged one-measurement → one-force → one-spring system. A visible WSLg/PulseAudio run held 62.4 FPS. Captures at the PulseAudio sink monitor were clean; Jorge's speaker-side check remains because that capture point cannot observe the downstream WSLg RDP transport.

**Completed work:**

- Added pygame-ce as the single lightweight playback/window/drawing dependency.
- Added `MusicPlayback` with start, pause/resume, elapsed playback position, completion detection, cleanup, and exact audio-output initialization. It performs no DSP and streams the original file.
- Added validated, configurable power-of-two playback buffering. The default is 4096 samples (92.9 ms at 44.1 kHz), replacing the fragile hard-coded 512-sample request.
- Added `PlaybackSynchronizedSpring`; it catches up skipped analysis frames, does not reintegrate repeated render frames, and deterministically resets/replays after a backward clock jump.
- Matured `python -m sound_springs.interactive` without adding a musical mapping: the existing spring now has a coil, marked equilibrium, force/velocity arrows, displacement history, progress display, and a `D`-toggleable diagnostic panel.
- Kept audio position, frame-center time, fixed simulation timestep, and render timing explicit and separate. No FFT runs in the render loop and no interpolation was added.
- Extended `DiagnosticRun` with playback backend, negotiated format, buffer size/latency, wall time, playback position, FPS/frame intervals, late frames, selected-frame offset, and process CPU metrics.
- Added focused playback configuration, synchronization, renderer-geometry, CLI, and diagnostic tests.
- Updated README, architecture, diagnostics, validation, and the work board with behavior, evidence, limitations, and the pygame-ce rationale.

**Tests:** `.venv/bin/pytest -q` passes 74 tests. `.venv/bin/python -m compileall -q src tests` and `git diff --check` pass.

**Experiments:** Playback was isolated with DSP, simulation, and rendering disabled, then compared with the full runtime. The source Cobra WAV is 44.1 kHz stereo signed PCM-16 and negotiates unchanged as 44100/-16/2 through pygame. FFplay control, pygame playback-only at 512 and 4096 samples, and full-runtime captures all reached the WSLg `RDPSink.monitor` without sustained zero runs or discontinuities. The revised visible eight-second run prepared 15,945 frames in 1.483 s and rendered at 62.4 FPS: 16.207/16.757 ms median/worst interval, zero intervals over 25 ms, 2.878/23.209 ms mean/max nearest-frame offset, and 6.2% one-core CPU. Evidence is under `_jorge_temp_dir/audio-probe/`; the renderer screenshot is under `_jorge_temp_dir/runtime-second-pass/`.

**Research findings:** The decoded analysis array is not handed to playback and no runtime processing modifies the heard samples. The clean sink-monitor captures rule out the DSP, simulation, renderer, normalization, clipping, and main-thread contention as the crackle source. Pygame exposes no underrun counter. The strongest practical diagnosis is the downstream WSLg PulseAudio-to-RDP path; this is an inference because the sink monitor is upstream of that boundary. The old 512-sample buffer was nevertheless an avoidable application-side risk, so the default is now 4096. The 23.209 ms maximum lookup offset is the expected first-frame center clamp, not observed drift.

**Known issues:** A clean `RDPSink.monitor` capture cannot prove that WSLg's later RDP transport and the physical speakers are clean; Jorge must make that acceptance check. The playback clock has millisecond resolution and is not an exact device sample cursor. Pause/resume exists; WAV seek does not. Pygame supplies no backend underrun/callback timing counter. Runtime diagnostics do not include the benchmark runner's RSS snapshots or retained-array sizes. The decoded float64 stereo memory behavior remains unchanged. Only one explicit channel and target bin drive one spring; peak normalization removes absolute loudness differences; the spring has no general stability guard. The renderer is an inspection view, not the eventual visual language.

**Open human decisions:** Jorge/Jon still own stereo meaning, musical measurements, spring count/coupling, phase/harmonics, and final visual geometry. The current view reveals force, inertia, damping, and return toward equilibrium but does not answer what additional musical quantities should mean physically. Also decide whether WAV seek is required before closing SS-101.

**Incomplete work:** SS-100 and SS-105 are complete. SS-101 remains in progress because seek is absent. SS-103 and SS-300 have real visible timing evidence and remain in progress only for Jorge's downstream speaker-side acceptance. Routine output, test audio, captures, and screenshots remain Git-ignored under `_jorge_temp_dir`.

**Recommended next task:** Run the revised command below and listen through Jorge's actual speakers. Watch whether the force/velocity arrows explain the bob's motion, toggle diagnostics with `D`, pause/resume once with Space, then exit with Esc. If audio is clean, close SS-103/SS-300. If it still crackles while the saved sink-monitor evidence is clean, investigate/update WSLg's downstream RDP audio path before changing DSP or the Sound Springs model.

**Important files:** `src/sound_springs/interactive.py`, `playback.py`, `runtime.py`, `diagnostics.py`; `tests/test_interactive.py`, `test_playback.py`, `test_runtime.py`; `docs/architecture.md`, `docs/diagnostics.md`, `docs/validation.md`, `docs/upcoming-work.md`.

**Useful commands:**

```bash
.venv/bin/python -m sound_springs.interactive \
  'test_audio/Geese_Getting_Killed/Cobra.wav' \
  --channel 0 \
  --audio-buffer-samples 4096 \
  --output-dir _jorge_temp_dir/interactive-second-pass \
  --run-id cobra-interactive-second-pass

TMPDIR=$PWD/_jorge_temp_dir/tmp PYGAME_HIDE_SUPPORT_PROMPT=1 \
  .venv/bin/pytest -q
.venv/bin/python -m compileall -q src tests
git diff --check
git status --short --branch
```
