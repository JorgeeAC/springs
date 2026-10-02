import csv
from pathlib import Path

import numpy as np
import soundfile as sf

from sound_springs.benchmark import benchmark_audio_file
from sound_springs.diagnostics import CSV_COLUMNS, DiagnosticRun
from sound_springs.pipeline import AnalysisSettings


def test_run_writes_one_complete_csv_row_and_text_summary(tmp_path: Path) -> None:
    run = DiagnosticRun(
        run_id="test-run",
        timestamp_utc="2026-10-02T12:00:00+00:00",
    )
    run.record("file_name", "song.wav")
    run.record("audio_duration_s", 123.5)
    run.record("file_size_bytes", 1_048_576)
    run.record("file_size_mib", 1.0)
    run.record("analysis_frame_count", 42)

    csv_path, text_path = run.write_outputs(tmp_path)

    assert sorted(path.suffix for path in tmp_path.iterdir()) == [".csv", ".txt"]
    with csv_path.open(encoding="utf-8", newline="") as csv_file:
        rows = list(csv.DictReader(csv_file))
    assert len(rows) == 1
    assert tuple(rows[0]) == CSV_COLUMNS
    assert rows[0]["run_id"] == "test-run"
    assert rows[0]["audio_duration_s"] == "123.5"
    assert rows[0]["peak_rss_mib"] == ""

    summary = text_path.read_text(encoding="utf-8")
    assert "Track: song.wav" in summary
    assert "Frames: 42" in summary
    assert "Peak process RSS: not available MiB" in summary


def test_generated_wav_exercises_runner_without_fragile_performance_assertions(
    tmp_path: Path,
) -> None:
    sample_rate = 8_192
    time = np.arange(sample_rate) / sample_rate
    samples = np.column_stack(
        (0.5 * np.sin(2 * np.pi * 440 * time), np.zeros(sample_rate))
    )
    audio_path = tmp_path / "fixture.wav"
    output_path = tmp_path / "runs"
    sf.write(audio_path, samples, sample_rate, subtype="PCM_16")

    run, csv_path, text_path = benchmark_audio_file(
        audio_path,
        output_path,
        channel=0,
        settings=AnalysisSettings(frame_length=1_024, hop_length=256),
        run_id="fixture-run",
    )

    assert csv_path == output_path / "fixture-run.csv"
    assert text_path == output_path / "fixture-run.txt"
    assert run.metrics["sample_rate_hz"] == sample_rate
    assert run.metrics["channel_count"] == 2
    assert run.metrics["decoded_dtype"] == "float64"
    assert run.metrics["analysis_frame_count"] == 29
    assert float(run.metrics["decode_s"]) >= 0
    assert float(run.metrics["timeline_s"]) >= 0
    assert float(run.metrics["dsp_analysis_s"]) >= 0
    pipeline_subphases = sum(
        float(run.metrics[name])
        for name in (
            "timeline_s",
            "dsp_analysis_s",
            "mapping_simulation_s",
        )
    )
    assert float(run.metrics["analysis_s"]) >= pipeline_subphases
    assert float(run.metrics["total_prepare_s"]) >= (
        float(run.metrics["decode_s"]) + float(run.metrics["analysis_s"])
    )
    assert int(run.metrics["precomputed_state_bytes"]) >= int(
        run.metrics["timeline_array_bytes"]
    )
