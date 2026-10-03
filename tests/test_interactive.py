from pathlib import Path

from sound_springs.diagnostics import DiagnosticRun
from sound_springs.interactive import (
    InteractiveRuntimeMetrics,
    build_argument_parser,
    record_runtime_metrics,
    spring_polyline,
)


def test_interactive_parser_keeps_file_and_channel_choice_explicit() -> None:
    options = build_argument_parser().parse_args(
        ["album/song.wav", "--channel", "1"]
    )

    assert options.audio_file == Path("album/song.wav")
    assert options.channel == 1
    assert options.fps == 60
    assert options.frequency == 440.0
    assert options.audio_buffer_samples == 4_096


def test_runtime_metrics_use_the_central_diagnostic_record() -> None:
    run = DiagnosticRun(run_id="interactive-test")
    metrics = InteractiveRuntimeMetrics(
        runtime_seconds=2.0,
        playback_position_end_seconds=1.9,
        render_frame_count=120,
        render_fps_average=60.0,
        render_frame_ms_median=16.6,
        render_frame_ms_worst=24.0,
        late_frame_count=1,
        analysis_frame_offset_ms_mean_abs=3.0,
        analysis_frame_offset_ms_max_abs=5.5,
        runtime_cpu_percent=4.0,
        audio_driver="test-pulse",
        audio_buffer_samples=4_096,
        audio_buffer_milliseconds=92.9,
        mixer_frequency_hz=44_100,
        mixer_sample_size_bits=-16,
        mixer_channel_count=2,
    )

    record_runtime_metrics(run, metrics, target_fps=60)

    assert run.metrics["interactive_runtime_s"] == 2.0
    assert run.metrics["playback_position_end_s"] == 1.9
    assert run.metrics["target_render_fps"] == 60
    assert run.metrics["render_frame_count"] == 120
    assert run.metrics["render_fps_average"] == 60.0
    assert run.metrics["render_frame_ms_median"] == 16.6
    assert run.metrics["render_frame_ms_worst"] == 24.0
    assert run.metrics["late_frame_count"] == 1
    assert run.metrics["analysis_frame_offset_ms_mean_abs"] == 3.0
    assert run.metrics["analysis_frame_offset_ms_max_abs"] == 5.5
    assert run.metrics["runtime_cpu_percent"] == 4.0
    assert run.metrics["audio_driver"] == "test-pulse"
    assert run.metrics["audio_buffer_samples"] == 4_096
    assert run.metrics["audio_buffer_ms"] == 92.9
    assert run.metrics["mixer_frequency_hz"] == 44_100
    assert run.metrics["mixer_sample_size_bits"] == -16
    assert run.metrics["mixer_channel_count"] == 2

    summary = run.text_summary()
    assert "Interactive runtime:" in summary
    assert "Average FPS: 60.0" in summary
    assert "Audio backend: test-pulse; 44100 Hz; -16-bit; 2 channel(s)" in summary
    assert "Audio buffer: 4096 samples / 92.9 ms" in summary


def test_spring_polyline_keeps_anchor_and_bob_while_showing_a_coil() -> None:
    points = spring_polyline(100, 500, 250, coil_count=8, amplitude=12)

    assert points[0] == (100, 250)
    assert points[-1] == (500, 250)
    coil_y_values = {point[1] for point in points[2:-2]}
    assert 238 in coil_y_values
    assert 262 in coil_y_values
    assert len(points) > 10
