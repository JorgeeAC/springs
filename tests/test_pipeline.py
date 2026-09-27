import numpy as np
import pytest

from sound_springs.pipeline import AnalysisSettings, run_pipeline
from sound_springs.signal import generate_sine


def test_pipeline_results_are_repeatable_and_read_only() -> None:
    sample_rate = 8_192
    signal = generate_sine(440.0, 0.5, sample_rate)
    settings = AnalysisSettings(frame_length=1_024, hop_length=256)

    first = run_pipeline(signal, sample_rate, settings)
    second = run_pipeline(signal, sample_rate, settings)

    np.testing.assert_array_equal(first.target_amplitudes, second.target_amplitudes)
    np.testing.assert_array_equal(first.forces, second.forces)
    np.testing.assert_array_equal(first.spring_positions, second.spring_positions)
    assert first.measured_frequency_hz == pytest.approx(440.0)
    with pytest.raises(ValueError, match="read-only"):
        first.forces[0] = 10.0


def test_silence_produces_no_force_or_spring_motion() -> None:
    result = run_pipeline(
        np.zeros(2_048),
        8_192,
        AnalysisSettings(frame_length=512, hop_length=128),
    )

    np.testing.assert_array_equal(result.target_amplitudes, 0.0)
    np.testing.assert_array_equal(result.forces, 0.0)
    np.testing.assert_array_equal(result.spring_positions, 0.0)


def test_pipeline_rejects_too_short_signal_and_frequency_above_nyquist() -> None:
    with pytest.raises(ValueError, match="complete frame"):
        run_pipeline(np.zeros(100), 44_100)
    with pytest.raises(ValueError, match="Nyquist"):
        run_pipeline(
            np.zeros(2_048),
            8_000,
            AnalysisSettings(target_frequency_hz=4_001.0),
        )
