"""Small complete audio-clock-driven interactive Sound Springs runtime."""

from __future__ import annotations

import argparse
from collections import deque
from collections.abc import Sequence
from dataclasses import dataclass
from pathlib import Path
from statistics import mean, median
from time import perf_counter, process_time

import pygame

from sound_springs.audio import (
    AudioBuffer,
    AudioDecodeError,
    load_audio_file,
    select_analysis_channel,
)
from sound_springs.diagnostics import DiagnosticRun, runtime_identity
from sound_springs.pipeline import AnalysisSettings, PipelineResult, run_pipeline
from sound_springs.playback import (
    DEFAULT_AUDIO_BUFFER_SAMPLES,
    AudioBackendInfo,
    AudioOutputSettings,
    MusicPlayback,
    initialize_audio_output,
)
from sound_springs.runtime import PlaybackSynchronizedSpring, RuntimeFrameState


WINDOW_SIZE = (1_100, 650)
BACKGROUND = (12, 16, 23)
PANEL = (24, 31, 42)
FOREGROUND = (231, 238, 245)
MUTED = (137, 151, 166)
GRID = (54, 66, 79)
SPRING_COLOR = (75, 208, 178)
BOB_COLOR = (251, 181, 79)
REST_COLOR = (105, 125, 145)
FORCE_COLOR = (244, 105, 119)
VELOCITY_COLOR = (111, 171, 255)
TRAIL_COLOR = (102, 119, 137)
TARGET_FPS = 60
POSITION_PIXELS_PER_UNIT = 3_000.0
VELOCITY_PIXELS_PER_UNIT = 900.0


@dataclass(frozen=True)
class InteractiveRuntimeMetrics:
    """Compact scalar evidence from one interactive loop."""

    runtime_seconds: float
    playback_position_end_seconds: float
    render_frame_count: int
    render_fps_average: float
    render_frame_ms_median: float | None
    render_frame_ms_worst: float | None
    late_frame_count: int
    analysis_frame_offset_ms_mean_abs: float | None
    analysis_frame_offset_ms_max_abs: float | None
    runtime_cpu_percent: float
    audio_driver: str
    audio_buffer_samples: int
    audio_buffer_milliseconds: float
    mixer_frequency_hz: int
    mixer_sample_size_bits: int
    mixer_channel_count: int


def _positive_float(value: str) -> float:
    parsed = float(value)
    if parsed <= 0:
        raise argparse.ArgumentTypeError("value must be positive")
    return parsed


def build_argument_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description=(
            "Precompute one WAV, play it, and drive the existing spring from "
            "the audio playback clock in a small pygame window."
        )
    )
    parser.add_argument("audio_file", type=Path, help="WAV file to play")
    parser.add_argument(
        "--channel",
        type=int,
        help="zero-based channel to analyze (required for multichannel input)",
    )
    parser.add_argument("--frequency", type=float, default=440.0)
    parser.add_argument("--frame-length", type=int, default=2_048)
    parser.add_argument("--hop-length", type=int, default=512)
    parser.add_argument("--fps", type=int, default=TARGET_FPS)
    parser.add_argument(
        "--audio-buffer-samples",
        type=int,
        default=DEFAULT_AUDIO_BUFFER_SAMPLES,
        help=(
            "SDL mixer buffer as a power-of-two sample count "
            f"(default: {DEFAULT_AUDIO_BUFFER_SAMPLES})"
        ),
    )
    parser.add_argument(
        "--output-dir",
        type=Path,
        default=Path("diagnostics/runs"),
        help="directory for one runtime CSV/TXT pair",
    )
    parser.add_argument("--run-id", help="optional stable artifact basename")
    parser.add_argument(
        "--max-runtime-seconds",
        type=_positive_float,
        help="stop after this wall-clock duration (useful for a smoke run)",
    )
    return parser


def prepare_runtime(
    audio_file: str | Path,
    channel: int | None,
    settings: AnalysisSettings,
    run: DiagnosticRun,
) -> tuple[AudioBuffer, int, PipelineResult]:
    """Decode and completely precompute before any playback begins."""
    audio_path = Path(audio_file)
    file_size_bytes = audio_path.stat().st_size
    python_version, platform_name = runtime_identity()
    run.record("file_name", audio_path.name)
    run.record("file_size_bytes", file_size_bytes)
    run.record("file_size_mib", file_size_bytes / (1024**2))
    run.record("frame_size_samples", settings.frame_length)
    run.record("hop_size_samples", settings.hop_length)
    run.record("fft_size_samples", settings.frame_length)
    run.record("target_frequency_hz", settings.target_frequency_hz)
    run.record("python_version", python_version)
    run.record("platform", platform_name)

    with run.measure("total_prepare_s"):
        with run.measure("decode_s"):
            audio = load_audio_file(audio_path)
        channel_index = select_analysis_channel(audio, channel)
        with run.measure("analysis_s"):
            result = run_pipeline(
                audio.channel(channel_index),
                audio.sample_rate,
                settings,
                diagnostics=run,
            )

    run.record("audio_duration_s", audio.duration_seconds)
    run.record("sample_rate_hz", audio.sample_rate)
    run.record("channel_count", audio.channel_count)
    run.record("analyzed_channel_index", channel_index)
    run.record("decoded_frame_count", audio.frame_count)
    run.record("decoded_sample_count", audio.samples.size)
    run.record("decoded_dtype", str(audio.samples.dtype))
    run.record("decoded_array_bytes", audio.samples.nbytes)
    run.record("decoded_array_mib", audio.samples.nbytes / (1024**2))
    run.record("fft_bin_count", len(result.frequencies))
    run.record("analysis_frame_count", result.timeline.frame_count)
    analysis_seconds = float(run.metrics["analysis_s"])
    run.record(
        "analysis_realtime_factor",
        audio.duration_seconds / analysis_seconds if analysis_seconds > 0 else None,
    )
    return audio, channel_index, result


def spring_polyline(
    anchor_x: int,
    bob_x: int,
    center_y: int,
    *,
    coil_count: int = 12,
    amplitude: int = 15,
) -> list[tuple[int, int]]:
    """Return a simple horizontal coil between an anchor and the spring bob."""
    if bob_x <= anchor_x:
        raise ValueError("bob_x must be to the right of anchor_x")
    if coil_count < 1:
        raise ValueError("coil_count must be positive")
    length = bob_x - anchor_x
    lead = min(36, max(8, length // 8))
    coil_start = anchor_x + lead
    coil_end = bob_x - lead
    points = [(anchor_x, center_y), (coil_start, center_y)]
    zigzag_count = coil_count * 2
    for index in range(1, zigzag_count):
        fraction = index / zigzag_count
        x = round(coil_start + (coil_end - coil_start) * fraction)
        y = center_y + (amplitude if index % 2 else -amplitude)
        points.append((x, y))
    points.extend(((coil_end, center_y), (bob_x, center_y)))
    return points


def _screen_x(position: float, rest_position: float, rest_x: int) -> int:
    displacement = position - rest_position
    return round(rest_x + displacement * POSITION_PIXELS_PER_UNIT)


def _draw_horizontal_arrow(
    surface: pygame.Surface,
    *,
    start: tuple[int, int],
    signed_length: float,
    color: tuple[int, int, int],
) -> None:
    length = int(max(-120, min(120, signed_length)))
    if abs(length) < 3:
        pygame.draw.circle(surface, color, start, 4)
        return
    end = (start[0] + length, start[1])
    pygame.draw.line(surface, color, start, end, width=4)
    direction = 1 if length > 0 else -1
    pygame.draw.polygon(
        surface,
        color,
        (
            end,
            (end[0] - direction * 11, end[1] - 7),
            (end[0] - direction * 11, end[1] + 7),
        ),
    )


def _draw_runtime(
    surface: pygame.Surface,
    font: pygame.font.Font,
    small_font: pygame.font.Font,
    *,
    state: RuntimeFrameState,
    playback: MusicPlayback,
    result: PipelineResult,
    file_name: str,
    displayed_fps: float,
    displacement_history: Sequence[float],
    show_debug: bool,
    audio_backend: AudioBackendInfo,
) -> None:
    """Draw the current one-force/one-spring experiment without new semantics."""
    surface.fill(BACKGROUND)
    width, height = surface.get_size()
    anchor_x = 135
    rest_x = width // 2
    center_y = 350
    bob_x = _screen_x(
        state.spring_position,
        state.spring_rest_position,
        rest_x,
    )
    bob_x = max(anchor_x + 80, min(width - 100, bob_x))

    pygame.draw.line(
        surface,
        GRID,
        (anchor_x, center_y),
        (width - 80, center_y),
        width=1,
    )
    for dash_y in range(center_y - 75, center_y + 76, 14):
        pygame.draw.line(
            surface,
            REST_COLOR,
            (rest_x, dash_y),
            (rest_x, min(dash_y + 7, center_y + 75)),
            width=2,
        )

    history_y = center_y + 118
    pygame.draw.line(
        surface,
        GRID,
        (anchor_x, history_y),
        (width - 80, history_y),
        width=1,
    )
    history_count = max(1, len(displacement_history))
    for index, position in enumerate(displacement_history):
        history_x = _screen_x(position, state.spring_rest_position, rest_x)
        history_x = max(anchor_x + 5, min(width - 85, history_x))
        brightness = 0.25 + 0.75 * (index + 1) / history_count
        color = tuple(round(component * brightness) for component in TRAIL_COLOR)
        pygame.draw.circle(surface, color, (history_x, history_y), 3)

    pygame.draw.lines(
        surface,
        SPRING_COLOR,
        False,
        spring_polyline(anchor_x, bob_x, center_y),
        width=4,
    )
    pygame.draw.circle(surface, FOREGROUND, (anchor_x, center_y), 10)
    pygame.draw.circle(surface, BOB_COLOR, (bob_x, center_y), 27)
    pygame.draw.circle(surface, FOREGROUND, (bob_x, center_y), 27, width=2)

    force_y = center_y - 78
    _draw_horizontal_arrow(
        surface,
        start=(bob_x, force_y),
        signed_length=state.force * 110,
        color=FORCE_COLOR,
    )
    velocity_y = center_y + 72
    _draw_horizontal_arrow(
        surface,
        start=(bob_x, velocity_y),
        signed_length=state.spring_velocity * VELOCITY_PIXELS_PER_UNIT,
        color=VELOCITY_COLOR,
    )

    surface.blit(
        small_font.render("audio force", True, FORCE_COLOR),
        (anchor_x, force_y - 12),
    )
    surface.blit(
        small_font.render("velocity", True, VELOCITY_COLOR),
        (anchor_x, velocity_y - 12),
    )
    surface.blit(
        small_font.render("recent displacement", True, MUTED),
        (anchor_x, history_y + 13),
    )
    rest_label = small_font.render("equilibrium x0", True, REST_COLOR)
    surface.blit(rest_label, (rest_x - rest_label.get_width() // 2, center_y - 105))

    status = "PAUSED" if playback.is_paused else "PLAYING"
    title = font.render("Sound Springs — one measured force, one spring", True, FOREGROUND)
    surface.blit(title, (34, 27))
    subtitle = small_font.render(
        (
            f"{file_name}  |  {status}  |  "
            f"{state.playback_time_seconds:7.2f} / "
            f"{playback.duration_seconds:7.2f} s  |  "
            f"{displayed_fps:4.1f} FPS"
        ),
        True,
        MUTED,
    )
    surface.blit(subtitle, (36, 66))

    displacement = state.spring_position - state.spring_rest_position
    state_line = small_font.render(
        (
            f"displacement x - x0 {displacement:+.5f}    "
            f"velocity {state.spring_velocity:+.5f}    "
            f"audio force {state.force:.5f}"
        ),
        True,
        FOREGROUND,
    )
    surface.blit(state_line, (anchor_x, center_y + 168))

    progress_left = 70
    progress_right = width - 70
    progress_y = height - 54
    pygame.draw.line(
        surface,
        GRID,
        (progress_left, progress_y),
        (progress_right, progress_y),
        width=6,
    )
    progress = min(1.0, state.playback_time_seconds / playback.duration_seconds)
    progress_x = round(progress_left + (progress_right - progress_left) * progress)
    pygame.draw.line(
        surface,
        SPRING_COLOR,
        (progress_left, progress_y),
        (progress_x, progress_y),
        width=6,
    )

    instruction = small_font.render(
        "Space pause/resume    D diagnostics    Esc or Q exit",
        True,
        MUTED,
    )
    surface.blit(instruction, (34, height - 31))

    if show_debug:
        panel_width = 385
        panel_height = 236
        panel_surface = pygame.Surface((panel_width, panel_height), pygame.SRCALPHA)
        panel_surface.fill((*PANEL, 238))
        debug_lines = (
            "TIMING / STATE",
            (
                f"audio {state.playback_time_seconds:.6f} s  |  "
                f"frame center {state.measurement.center_time_seconds:.6f} s"
            ),
            (
                f"offset "
                f"{(state.measurement.center_time_seconds - state.playback_time_seconds) * 1_000:+.3f} ms"
            ),
            (
                f"analysis frame {state.measurement.frame_index}  |  "
                f"simulation dt {result.timestep_seconds * 1_000:.3f} ms"
            ),
            (
                f"{state.measurement.frequency_hz:.2f} Hz amplitude "
                f"{state.measurement.target_amplitude:.7f}"
            ),
            f"mapped force {state.force:.7f}",
            f"position {state.spring_position:+.7f}",
            f"velocity {state.spring_velocity:+.7f}",
            "",
            (
                f"audio {audio_backend.driver}: "
                f"{audio_backend.mixer_frequency_hz} Hz / "
                f"{audio_backend.mixer_sample_size_bits}-bit / "
                f"{audio_backend.mixer_channel_count} ch"
            ),
            (
                f"buffer {audio_backend.buffer_samples} samples / "
                f"{audio_backend.buffer_milliseconds:.1f} ms"
            ),
        )
        for index, line in enumerate(debug_lines):
            color = FOREGROUND if index == 0 else MUTED
            rendered = small_font.render(line, True, color)
            panel_surface.blit(rendered, (15, 12 + index * 19))
        surface.blit(panel_surface, (width - panel_width - 25, 20))


def run_interactive_loop(
    audio_file: str | Path,
    audio: AudioBuffer,
    result: PipelineResult,
    *,
    target_fps: int = TARGET_FPS,
    audio_buffer_samples: int = DEFAULT_AUDIO_BUFFER_SAMPLES,
    max_runtime_seconds: float | None = None,
) -> InteractiveRuntimeMetrics:
    """Play, synchronize, simulate, and render until the song or user exits."""
    if target_fps <= 0:
        raise ValueError("target_fps must be positive")

    audio_settings = AudioOutputSettings(
        sample_rate=audio.sample_rate,
        source_channel_count=audio.channel_count,
        buffer_samples=audio_buffer_samples,
    )
    pygame.display.init()
    pygame.font.init()
    try:
        audio_backend = initialize_audio_output(audio_settings)
        screen = pygame.display.set_mode(WINDOW_SIZE)
    except Exception:
        pygame.quit()
        raise

    pygame.display.set_caption("Sound Springs")
    font = pygame.font.Font(None, 34)
    small_font = pygame.font.Font(None, 23)
    clock = pygame.time.Clock()
    synchronized_spring = PlaybackSynchronizedSpring(result)
    displacement_history: deque[float] = deque(maxlen=64)
    history_frame_index = -1
    show_debug = False

    frame_intervals_seconds: list[float] = []
    analysis_offsets_seconds: list[float] = []
    frame_count = 0
    playback_position = 0.0
    previous_frame_started: float | None = None
    wall_started = perf_counter()
    cpu_started = process_time()

    try:
        with MusicPlayback(audio_file, audio.duration_seconds) as playback:
            playback.play()
            running = True
            while running:
                frame_started = perf_counter()
                if previous_frame_started is not None:
                    frame_intervals_seconds.append(
                        frame_started - previous_frame_started
                    )
                previous_frame_started = frame_started

                for event in pygame.event.get():
                    if event.type == pygame.QUIT:
                        running = False
                    elif event.type == pygame.KEYDOWN:
                        if event.key in (pygame.K_ESCAPE, pygame.K_q):
                            running = False
                        elif event.key == pygame.K_SPACE:
                            playback.toggle_pause()
                        elif event.key == pygame.K_d:
                            show_debug = not show_debug
                if not running:
                    break

                playback_position = playback.position_seconds
                state = synchronized_spring.advance_to(playback_position)
                if state.measurement.frame_index != history_frame_index:
                    displacement_history.append(state.spring_position)
                    history_frame_index = state.measurement.frame_index
                analysis_offsets_seconds.append(
                    state.measurement.center_time_seconds - playback_position
                )
                _draw_runtime(
                    screen,
                    font,
                    small_font,
                    state=state,
                    playback=playback,
                    result=result,
                    file_name=Path(audio_file).name,
                    displayed_fps=clock.get_fps(),
                    displacement_history=displacement_history,
                    show_debug=show_debug,
                    audio_backend=audio_backend,
                )
                pygame.display.flip()
                frame_count += 1

                elapsed = perf_counter() - wall_started
                if playback.is_finished:
                    running = False
                elif (
                    max_runtime_seconds is not None
                    and elapsed >= max_runtime_seconds
                ):
                    running = False
                if running:
                    clock.tick(target_fps)
    finally:
        loop_ended = perf_counter()
        cpu_ended = process_time()
        pygame.quit()

    runtime_seconds = loop_ended - wall_started
    cpu_seconds = cpu_ended - cpu_started
    frame_milliseconds = [
        duration * 1_000 for duration in frame_intervals_seconds
    ]
    absolute_offset_milliseconds = [
        abs(offset) * 1_000 for offset in analysis_offsets_seconds
    ]
    late_threshold_seconds = 1.5 / target_fps
    return InteractiveRuntimeMetrics(
        runtime_seconds=runtime_seconds,
        playback_position_end_seconds=playback_position,
        render_frame_count=frame_count,
        render_fps_average=(
            frame_count / runtime_seconds if runtime_seconds > 0 else 0.0
        ),
        render_frame_ms_median=(
            median(frame_milliseconds) if frame_milliseconds else None
        ),
        render_frame_ms_worst=(
            max(frame_milliseconds) if frame_milliseconds else None
        ),
        late_frame_count=sum(
            interval > late_threshold_seconds
            for interval in frame_intervals_seconds
        ),
        analysis_frame_offset_ms_mean_abs=(
            mean(absolute_offset_milliseconds)
            if absolute_offset_milliseconds
            else None
        ),
        analysis_frame_offset_ms_max_abs=(
            max(absolute_offset_milliseconds)
            if absolute_offset_milliseconds
            else None
        ),
        runtime_cpu_percent=(
            cpu_seconds / runtime_seconds * 100 if runtime_seconds > 0 else 0.0
        ),
        audio_driver=audio_backend.driver,
        audio_buffer_samples=audio_backend.buffer_samples,
        audio_buffer_milliseconds=audio_backend.buffer_milliseconds,
        mixer_frequency_hz=audio_backend.mixer_frequency_hz,
        mixer_sample_size_bits=audio_backend.mixer_sample_size_bits,
        mixer_channel_count=audio_backend.mixer_channel_count,
    )


def record_runtime_metrics(
    run: DiagnosticRun,
    metrics: InteractiveRuntimeMetrics,
    *,
    target_fps: int,
) -> None:
    """Add the interactive loop's scalar evidence to the shared run record."""
    run.record("interactive_runtime_s", metrics.runtime_seconds)
    run.record(
        "playback_position_end_s",
        metrics.playback_position_end_seconds,
    )
    run.record("target_render_fps", target_fps)
    run.record("render_frame_count", metrics.render_frame_count)
    run.record("render_fps_average", metrics.render_fps_average)
    run.record("render_frame_ms_median", metrics.render_frame_ms_median)
    run.record("render_frame_ms_worst", metrics.render_frame_ms_worst)
    run.record("late_frame_count", metrics.late_frame_count)
    run.record(
        "analysis_frame_offset_ms_mean_abs",
        metrics.analysis_frame_offset_ms_mean_abs,
    )
    run.record(
        "analysis_frame_offset_ms_max_abs",
        metrics.analysis_frame_offset_ms_max_abs,
    )
    run.record("runtime_cpu_percent", metrics.runtime_cpu_percent)
    run.record("audio_driver", metrics.audio_driver)
    run.record("audio_buffer_samples", metrics.audio_buffer_samples)
    run.record("audio_buffer_ms", metrics.audio_buffer_milliseconds)
    run.record("mixer_frequency_hz", metrics.mixer_frequency_hz)
    run.record("mixer_sample_size_bits", metrics.mixer_sample_size_bits)
    run.record("mixer_channel_count", metrics.mixer_channel_count)


def main(arguments: Sequence[str] | None = None) -> None:
    parser = build_argument_parser()
    options = parser.parse_args(arguments)
    if options.fps <= 0:
        parser.error("--fps must be positive")

    run = DiagnosticRun() if options.run_id is None else DiagnosticRun(options.run_id)
    try:
        settings = AnalysisSettings(
            frame_length=options.frame_length,
            hop_length=options.hop_length,
            target_frequency_hz=options.frequency,
        )
        audio, channel_index, result = prepare_runtime(
            options.audio_file,
            options.channel,
            settings,
            run,
        )
        print(
            f"Prepared {options.audio_file.name}: "
            f"{result.timeline.frame_count} frames; channel {channel_index}; "
            f"{float(run.metrics['total_prepare_s']):.3f} s"
        )
        metrics = run_interactive_loop(
            options.audio_file,
            audio,
            result,
            target_fps=options.fps,
            audio_buffer_samples=options.audio_buffer_samples,
            max_runtime_seconds=options.max_runtime_seconds,
        )
        record_runtime_metrics(run, metrics, target_fps=options.fps)
        csv_path, text_path = run.write_outputs(options.output_dir)
    except (
        AudioDecodeError,
        FileNotFoundError,
        OSError,
        RuntimeError,
        ValueError,
        pygame.error,
    ) as error:
        pygame.quit()
        parser.error(str(error))

    print(
        f"Runtime: {metrics.runtime_seconds:.3f} s; "
        f"average FPS: {metrics.render_fps_average:.1f}; "
        f"worst frame: "
        f"{metrics.render_frame_ms_worst or 0.0:.3f} ms; "
        f"late frames: {metrics.late_frame_count}"
    )
    print(
        f"Audio: {metrics.audio_driver}; "
        f"{metrics.mixer_frequency_hz} Hz; "
        f"{metrics.mixer_sample_size_bits}-bit; "
        f"{metrics.mixer_channel_count} channel(s); "
        f"{metrics.audio_buffer_samples} samples "
        f"({metrics.audio_buffer_milliseconds:.1f} ms)"
    )
    print(f"CSV: {csv_path}")
    print(f"TXT: {text_path}")


if __name__ == "__main__":
    main()
