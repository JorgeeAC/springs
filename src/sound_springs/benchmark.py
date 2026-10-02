"""Benchmark one real audio file through the current precompute pipeline."""

from __future__ import annotations

import argparse
import gc
from collections.abc import Sequence
from pathlib import Path

from sound_springs.audio import (
    AudioDecodeError,
    load_audio_file,
    select_analysis_channel,
)
from sound_springs.diagnostics import (
    DiagnosticRun,
    ProcessMemorySnapshot,
    process_memory_snapshot,
    runtime_identity,
)
from sound_springs.pipeline import AnalysisSettings, PipelineResult, run_pipeline


MIB = 1024**2


def _record_memory(
    run: DiagnosticRun,
    metric_name: str,
    snapshot: ProcessMemorySnapshot,
) -> None:
    run.record(metric_name, snapshot.current_rss_mib)


def _record_delta(
    run: DiagnosticRun,
    metric_name: str,
    before: float | None,
    after: float | None,
) -> None:
    run.record(
        metric_name,
        None if before is None or after is None else after - before,
    )


def _timeline_array_bytes(result: PipelineResult) -> int:
    timeline = result.timeline
    return sum(
        values.nbytes
        for values in (
            timeline.start_samples,
            timeline.end_samples_exclusive,
            timeline.center_samples,
            timeline.center_times_seconds,
        )
    )


def _precomputed_state_bytes(result: PipelineResult) -> int:
    result_arrays = (
        result.frequencies,
        result.representative_amplitudes,
        result.target_amplitudes,
        result.forces,
        result.spring_positions,
    )
    return _timeline_array_bytes(result) + sum(values.nbytes for values in result_arrays)


def benchmark_audio_file(
    audio_file: str | Path,
    output_directory: str | Path = Path("diagnostics/runs"),
    *,
    channel: int | None = None,
    settings: AnalysisSettings = AnalysisSettings(),
    run_id: str | None = None,
) -> tuple[DiagnosticRun, Path, Path]:
    """Measure one decode/precompute run and write its CSV/TXT artifacts."""
    audio_path = Path(audio_file)
    run = DiagnosticRun() if run_id is None else DiagnosticRun(run_id=run_id)
    python_version, platform_name = runtime_identity()
    file_size_bytes = audio_path.stat().st_size
    run.record("file_name", audio_path.name)
    run.record("file_size_bytes", file_size_bytes)
    run.record("file_size_mib", file_size_bytes / MIB)
    run.record("frame_size_samples", settings.frame_length)
    run.record("hop_size_samples", settings.hop_length)
    run.record("fft_size_samples", settings.frame_length)
    run.record("target_frequency_hz", settings.target_frequency_hz)
    run.record("python_version", python_version)
    run.record("platform", platform_name)

    before_load = process_memory_snapshot()
    _record_memory(run, "memory_before_load_rss_mib", before_load)
    run.record("current_rss_source", before_load.current_source)
    run.record("peak_rss_source", before_load.peak_source)

    with run.measure("total_prepare_s"):
        with run.measure("decode_s"):
            audio = load_audio_file(audio_path)
        after_decode = process_memory_snapshot()
        _record_memory(run, "memory_after_decode_rss_mib", after_decode)

        channel_index = select_analysis_channel(audio, channel)
        signal = audio.channel(channel_index)
        with run.measure("analysis_s"):
            result = run_pipeline(
                signal,
                audio.sample_rate,
                settings,
                diagnostics=run,
            )
        after_analysis = process_memory_snapshot()
        _record_memory(run, "memory_after_analysis_rss_mib", after_analysis)

    run.record("audio_duration_s", audio.duration_seconds)
    run.record("sample_rate_hz", audio.sample_rate)
    run.record("channel_count", audio.channel_count)
    run.record("analyzed_channel_index", channel_index)
    run.record("decoded_frame_count", audio.frame_count)
    run.record("decoded_sample_count", audio.samples.size)
    run.record("decoded_dtype", str(audio.samples.dtype))
    run.record("decoded_array_bytes", audio.samples.nbytes)
    run.record("decoded_array_mib", audio.samples.nbytes / MIB)
    run.record("fft_bin_count", len(result.frequencies))
    run.record("analysis_frame_count", result.timeline.frame_count)

    timeline_bytes = _timeline_array_bytes(result)
    precomputed_bytes = _precomputed_state_bytes(result)
    run.record("timeline_array_bytes", timeline_bytes)
    run.record("timeline_array_mib", timeline_bytes / MIB)
    run.record("precomputed_state_bytes", precomputed_bytes)
    run.record("precomputed_state_mib", precomputed_bytes / MIB)

    analysis_seconds = float(run.metrics["analysis_s"])
    run.record(
        "analysis_realtime_factor",
        audio.duration_seconds / analysis_seconds if analysis_seconds > 0 else None,
    )
    _record_delta(
        run,
        "decode_rss_delta_mib",
        before_load.current_rss_mib,
        after_decode.current_rss_mib,
    )
    _record_delta(
        run,
        "analysis_rss_delta_mib",
        after_decode.current_rss_mib,
        after_analysis.current_rss_mib,
    )
    _record_delta(
        run,
        "total_prepare_rss_delta_mib",
        before_load.current_rss_mib,
        after_analysis.current_rss_mib,
    )

    del signal, result, audio
    gc.collect()
    end = process_memory_snapshot()
    _record_memory(run, "memory_end_rss_mib", end)
    peak_values = (
        snapshot.peak_rss_mib
        for snapshot in (before_load, after_decode, after_analysis, end)
        if snapshot.peak_rss_mib is not None
    )
    run.record("peak_rss_mib", max(peak_values, default=None))
    _record_delta(
        run,
        "release_rss_delta_mib",
        after_analysis.current_rss_mib,
        end.current_rss_mib,
    )

    csv_path, text_path = run.write_outputs(output_directory)
    return run, csv_path, text_path


def build_argument_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Benchmark one WAV or FLAC through the current precompute path."
    )
    parser.add_argument("audio_file", type=Path)
    parser.add_argument(
        "--channel",
        type=int,
        help="zero-based channel to analyze (required for multichannel input)",
    )
    parser.add_argument("--frequency", type=float, default=440.0)
    parser.add_argument("--frame-length", type=int, default=2_048)
    parser.add_argument("--hop-length", type=int, default=512)
    parser.add_argument(
        "--output-dir",
        type=Path,
        default=Path("diagnostics/runs"),
    )
    parser.add_argument("--run-id", help="optional stable artifact basename")
    return parser


def main(arguments: Sequence[str] | None = None) -> None:
    parser = build_argument_parser()
    options = parser.parse_args(arguments)
    try:
        settings = AnalysisSettings(
            frame_length=options.frame_length,
            hop_length=options.hop_length,
            target_frequency_hz=options.frequency,
        )
        run, csv_path, text_path = benchmark_audio_file(
            options.audio_file,
            options.output_dir,
            channel=options.channel,
            settings=settings,
            run_id=options.run_id,
        )
    except (AudioDecodeError, FileNotFoundError, OSError, ValueError) as error:
        parser.error(str(error))

    print(run.text_summary(), end="")
    print(f"CSV: {csv_path}")
    print(f"TXT: {text_path}")


if __name__ == "__main__":
    main()
