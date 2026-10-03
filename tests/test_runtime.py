import numpy as np
import pytest

from sound_springs.pipeline import AnalysisSettings, run_pipeline
from sound_springs.runtime import PlaybackSynchronizedSpring


def _result():
    sample_rate = 8_000
    duration_seconds = 0.5
    time = np.arange(int(sample_rate * duration_seconds)) / sample_rate
    signal = np.sin(2 * np.pi * 440 * time)
    return run_pipeline(
        signal,
        sample_rate,
        AnalysisSettings(frame_length=400, hop_length=80),
    )


def test_runtime_applies_each_precomputed_force_once_in_fixed_hop_steps() -> None:
    result = _result()
    runtime = PlaybackSynchronizedSpring(result)
    selected_index = 10

    state = runtime.advance_to(result.measurement_times_seconds[selected_index])

    assert state.measurement.frame_index == selected_index
    assert state.force == result.forces[selected_index]
    assert state.spring_position == pytest.approx(
        result.spring_positions[selected_index]
    )
    assert runtime.simulated_through_frame_index == selected_index

    repeated = runtime.advance_to(result.measurement_times_seconds[selected_index])
    assert repeated.spring_position == state.spring_position
    assert runtime.simulated_through_frame_index == selected_index


def test_runtime_catches_up_when_rendering_skips_analysis_frames() -> None:
    result = _result()
    runtime = PlaybackSynchronizedSpring(result)

    runtime.advance_to(result.measurement_times_seconds[2])
    state = runtime.advance_to(result.measurement_times_seconds[20])

    assert state.spring_position == pytest.approx(result.spring_positions[20])
    assert runtime.simulated_through_frame_index == 20


def test_backward_clock_jump_resets_and_replays_deterministically() -> None:
    result = _result()
    runtime = PlaybackSynchronizedSpring(result)

    runtime.advance_to(result.measurement_times_seconds[20])
    state = runtime.advance_to(result.measurement_times_seconds[5])

    assert state.measurement.frame_index == 5
    assert state.spring_position == pytest.approx(result.spring_positions[5])
    assert runtime.simulated_through_frame_index == 5


def test_runtime_uses_timeline_validation_for_invalid_playback_time() -> None:
    result = _result()
    runtime = PlaybackSynchronizedSpring(result)

    with pytest.raises(ValueError, match="playback_time_seconds"):
        runtime.advance_to(-0.1)
