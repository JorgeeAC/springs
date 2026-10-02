# Runtime diagnostics

Sound Springs has one deliberately small metrics funnel:

    benchmark runner and instrumented pipeline phases
        → DiagnosticRun scalar record
        → one CSV row + one TXT summary

DiagnosticRun owns metric names, elapsed-time collection, and serialization.
The audio loader, DSP functions, timeline, mapping, and spring do not write
files. run_pipeline accepts an optional record only to bracket its existing
timeline, DSP, and mapping/simulation phases. Tests verify that enabling these
timers leaves every deterministic result array unchanged.

Run one file with:

    python -m sound_springs.benchmark path/to/song.wav --channel 0

Mono files do not need --channel. The defaults remain a 2,048-sample frame,
512-sample hop, and 440 Hz target. Output is written to
diagnostics/runs/<run-id>.csv and .txt; the source audio stays in place.
Routine files in diagnostics/runs are Git-ignored. They are working evidence,
not project history. One compact, reviewed album summary is tracked under
diagnostics/baselines; individual track CSV/TXT pairs should not be committed.

## CSV schema

The CSV is canonical and contains one row. Its stable column order is:

    run_id
    timestamp_utc
    file_name
    audio_duration_s
    file_size_bytes
    file_size_mib
    sample_rate_hz
    channel_count
    analyzed_channel_index
    decoded_frame_count
    decoded_sample_count
    decoded_dtype
    decoded_array_bytes
    decoded_array_mib
    decode_s
    analysis_s
    dsp_analysis_s
    timeline_s
    mapping_simulation_s
    total_prepare_s
    analysis_realtime_factor
    frame_size_samples
    hop_size_samples
    fft_size_samples
    fft_bin_count
    target_frequency_hz
    analysis_frame_count
    timeline_array_bytes
    timeline_array_mib
    precomputed_state_bytes
    precomputed_state_mib
    memory_before_load_rss_mib
    memory_after_decode_rss_mib
    memory_after_analysis_rss_mib
    memory_end_rss_mib
    peak_rss_mib
    decode_rss_delta_mib
    analysis_rss_delta_mib
    total_prepare_rss_delta_mib
    release_rss_delta_mib
    current_rss_source
    peak_rss_source
    python_version
    platform

decoded_frame_count counts sample frames (one frame contains all channels);
decoded_sample_count counts scalar channel samples. analysis_s covers the
complete run_pipeline call. Its measured subphases are timeline_s,
dsp_analysis_s, and mapping_simulation_s; validation, result construction, and
timer overhead make the complete time slightly larger than their sum.
total_prepare_s covers decode, channel selection, the pipeline call, and the two
surrounding memory snapshots. Realtime factor is audio duration divided by
analysis_s.

The exact NumPy payload sizes are reported separately:

- decoded_array_bytes is the retained float64 PCM array.
- timeline_array_bytes is the four retained timeline coordinate arrays.
- precomputed_state_bytes is all retained timeline and PipelineResult NumPy
  arrays. It excludes Python object overhead and temporary FFT arrays.

## Process memory meaning

On Linux, current RSS comes from VmRSS in /proc/self/status. It is the physical
memory resident for the whole benchmark process at that observation, including
Python, imported libraries, native allocations, allocator-retained pages,
decoded PCM, and precomputed state. It is not object attribution.

Peak RSS comes from VmHWM in the same file. It is the high-water mark since
process start, not merely since audio loading, and includes transient buffers.
All fields ending in _mib divide bytes by 1,048,576. Deltas are later snapshot
minus earlier snapshot and may be negative:

- decode_rss_delta_mib: post-decode minus pre-load;
- analysis_rss_delta_mib: post-analysis minus post-decode;
- total_prepare_rss_delta_mib: post-analysis minus pre-load;
- release_rss_delta_mib: post-release minus post-analysis.

The end snapshot is taken after references to the audio and pipeline result are
deleted and Python garbage collection runs, but before output is serialized. A
nonzero end delta does not prove a leak: Python/native allocators and the
operating system may keep released pages resident.

Platforms without /proc/self/status leave these optional process-memory fields
empty rather than substituting a metric with different semantics.

## First real-WAV baseline

Run 20261002-getting-killed-title-track used Getting Killed.wav from the local,
Git-ignored test_audio/Geese_Getting_Killed album copy. It is a 284.533-second,
44.1 kHz, stereo PCM-16 WAV; channel 0 was analyzed under the explicit-channel
policy.

- file size: 47.867 MiB
- decoded float64 PCM: 191.466 MiB
- decode: 0.409 s
- complete pipeline analysis: 1.936 s, or 147.0x realtime
- DSP subphase: 1.904 s
- timeline construction: 0.002 s
- mapping/simulation: 0.016 s
- complete frames: 24,504
- retained precomputed arrays: 1.324 MiB, including a 0.748 MiB timeline
- RSS: 29.582 MiB before load, 221.426 MiB after decode, and 233.980 MiB after
  analysis
- process-lifetime peak RSS: 412.836 MiB
- RSS after releasing the song/result and collecting: 42.535 MiB

The retained live-state RSS increase was 204.398 MiB, dominated by the 191.466
MiB decoded stereo array rather than the 1.324 MiB precomputed result. The much
higher peak is consistent with transient decode ownership: soundfile creates a
float64 array and AudioBuffer then takes its immutable owned copy, so two
roughly 191 MiB arrays may briefly coexist. This is an observation, not a
per-allocation profiler result.

## Getting Killed album baseline

Every WAV in the 11-track album was run through the unchanged CLI in a separate
Python process so VmHWM from one song could not contaminate another. The
canonical aggregate is
[20261002-getting-killed-album-summary.csv](../diagnostics/baselines/20261002-getting-killed-album-summary.csv);
the companion interpretation is
[20261002-getting-killed-album-summary.txt](../diagnostics/baselines/20261002-getting-killed-album-summary.txt).
The aggregate CSV retains one row per track; repetitive raw per-track run pairs
remain local and ignored.

Measured facts:

- total duration was 2,742.453 seconds (45:42.453);
- preparation time median/max was 1.468/2.731 seconds;
- analysis realtime factor median/minimum was 177.6x/169.9x;
- retained precomputed state ranged from 0.867 to 1.851 MiB;
- live-state RSS increase median/max was 162.367/272.844 MiB;
- peak RSS median/max was 333.535/566.727 MiB;
- decoded PCM reached 268.546 MiB on the longest 399.080-second track;
- three of 11 tracks exceeded 400 MiB peak RSS;
- post-release RSS median/range was 39.152/33.672-45.086 MiB.

Full-song analysis is consistently fast across this album. Decoded PCM scales
at exactly 0.672913 MiB per second for these 44.1 kHz stereo files and is about
3.99997 times the PCM-16 WAV file size because two-byte samples are retained as
eight-byte float64 values. Peak RSS also scales with decoded size. The original
approximately 400 MiB title-track peak is above the album median but is not
anomalous; longer tracks reached 506 and 567 MiB.

The likely cause of the roughly doubled transient cost remains the soundfile
array and AudioBuffer's immutable owned copy briefly coexisting. Peak RSS minus
twice decoded PCM left a 29.530 MiB median residual, close to the process
baseline. Process RSS cannot prove allocation ownership, so this remains a
supported explanation rather than a profiler result. After release, every
fresh process returned to 33.7-45.1 MiB, with a median 9.828 MiB remaining above
its pre-load baseline; there is no album evidence of resident memory
accumulating across tracks.

No decoding, representation, DSP, timeline, simulation, streaming, or chunking
change is justified now. Every song completed and even the slowest analysis was
169.9x realtime. The 566.727 MiB worst peak does justify defining target
platform memory budgets. If that budget proves too small, avoiding the transient
owned-copy overlap, lower precision, or selected-channel decoding are narrower
future experiments before a streaming redesign.

Method limits: each track was measured once on one WSL/Linux machine, the files
share 44.1 kHz stereo PCM-16 encoding, filesystem cache and system load were not
controlled, and RSS is process-level rather than allocation attribution.
