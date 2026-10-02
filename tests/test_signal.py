import numpy as np
import pytest

from sound_springs.signal import generate_linear_chirp, generate_silence, generate_sine
from sound_springs.spectrum import analyze_frames, frame_signal


def test_linear_chirp_moves_dominant_frequency_upward() -> None:
    sample_rate = 8_192
    signal = generate_linear_chirp(256.0, 1_536.0, 1.0, sample_rate)
    frames = frame_signal(signal, frame_length=512, hop_length=512)

    frequencies, amplitudes = analyze_frames(frames, sample_rate)
    dominant_frequencies = frequencies[np.argmax(amplitudes, axis=1)]

    assert dominant_frequencies[0] == pytest.approx(288.0, abs=16.0)
    assert dominant_frequencies[-1] == pytest.approx(1_504.0, abs=16.0)
    assert np.all(np.diff(dominant_frequencies) > 0)


def test_signal_generators_reject_aliasing_and_non_finite_inputs() -> None:
    with pytest.raises(ValueError, match="Nyquist"):
        generate_sine(4_001.0, 1.0, 8_000)
    with pytest.raises(ValueError, match="finite"):
        generate_linear_chirp(100.0, 200.0, float("nan"), 8_000)


def test_zero_duration_chirp_is_empty() -> None:
    assert generate_linear_chirp(100.0, 200.0, 0.0, 8_000).size == 0


def test_configurable_sine_amplitude_and_silence_are_deterministic() -> None:
    first = generate_sine(1_000.0, 0.25, 8_000, amplitude=0.25)
    second = generate_sine(1_000.0, 0.25, 8_000, amplitude=0.25)

    np.testing.assert_array_equal(first, second)
    assert np.max(first) == pytest.approx(0.25)
    np.testing.assert_array_equal(generate_silence(0.25, 8_000), 0.0)


def test_sine_rejects_invalid_amplitude() -> None:
    with pytest.raises(ValueError, match="amplitude"):
        generate_sine(440.0, 1.0, 8_000, amplitude=-0.1)
