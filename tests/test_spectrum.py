import numpy as np
import pytest

from sound_springs.signal import generate_sine
from sound_springs.spectrum import analyze_frame, analyze_frames, frame_signal


def test_strongest_frequency_is_near_generated_frequency() -> None:
    sample_rate = 44_100
    frame_length = 2048
    signal = generate_sine(440.0, frame_length / sample_rate, sample_rate)

    frequencies, magnitudes = analyze_frame(signal, sample_rate)
    strongest_frequency = frequencies[np.argmax(magnitudes)]
    frequency_resolution = sample_rate / frame_length

    assert abs(strongest_frequency - 440.0) <= frequency_resolution


def test_bin_centered_sine_reports_its_amplitude() -> None:
    sample_rate = 8_192
    frame_length = 1_024
    expected_amplitude = 0.4
    signal = expected_amplitude * generate_sine(
        1_000.0,
        frame_length / sample_rate,
        sample_rate,
    )

    frequencies, amplitudes = analyze_frame(signal, sample_rate)
    target_bin = int(np.argmin(np.abs(frequencies - 1_000.0)))

    assert frequencies[target_bin] == pytest.approx(1_000.0)
    assert amplitudes[target_bin] == pytest.approx(expected_amplitude, rel=2e-6)


def test_two_tone_signal_has_both_expected_amplitudes() -> None:
    sample_rate = 8_192
    frame_length = 1_024
    first = 0.6 * generate_sine(440.0, frame_length / sample_rate, sample_rate)
    second = 0.2 * generate_sine(880.0, frame_length / sample_rate, sample_rate)

    frequencies, amplitudes = analyze_frame(first + second, sample_rate)
    first_bin = int(np.argmin(np.abs(frequencies - 440.0)))
    second_bin = int(np.argmin(np.abs(frequencies - 880.0)))

    assert amplitudes[first_bin] == pytest.approx(0.6, rel=2e-6)
    assert amplitudes[second_bin] == pytest.approx(0.2, rel=2e-6)


def test_silence_has_zero_amplitude_and_analysis_is_repeatable() -> None:
    frames = np.zeros((3, 1_024))

    first_frequencies, first_amplitudes = analyze_frames(frames, 44_100)
    second_frequencies, second_amplitudes = analyze_frames(frames, 44_100)

    np.testing.assert_array_equal(first_amplitudes, 0.0)
    np.testing.assert_array_equal(first_frequencies, second_frequencies)
    np.testing.assert_array_equal(first_amplitudes, second_amplitudes)


def test_framing_starts_at_each_hop() -> None:
    signal = np.arange(4096)

    frames = frame_signal(signal, frame_length=2048, hop_length=512)

    np.testing.assert_array_equal(frames[0], signal[0:2048])
    np.testing.assert_array_equal(frames[1], signal[512:2560])
    np.testing.assert_array_equal(frames[2], signal[1024:3072])


def test_framing_drops_incomplete_final_frame() -> None:
    signal = np.arange(2048 + 511)

    frames = frame_signal(signal, frame_length=2048, hop_length=512)

    assert len(frames) == 1


def test_analysis_rejects_invalid_or_non_finite_frames() -> None:
    with pytest.raises(ValueError, match="at least 3"):
        analyze_frame(np.zeros(2), 44_100)
    with pytest.raises(ValueError, match="finite"):
        analyze_frame(np.array([0.0, np.inf, 0.0]), 44_100)
    with pytest.raises(ValueError, match="at least one"):
        analyze_frames(np.empty((0, 1_024)), 44_100)
