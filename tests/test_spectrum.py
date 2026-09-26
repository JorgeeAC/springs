import numpy as np

from sound_springs.signal import generate_sine
from sound_springs.spectrum import analyze_frame, frame_signal


def test_strongest_frequency_is_near_generated_frequency() -> None:
    sample_rate = 44_100
    frame_length = 2048
    signal = generate_sine(440.0, frame_length / sample_rate, sample_rate)

    frequencies, magnitudes = analyze_frame(signal, sample_rate)
    strongest_frequency = frequencies[np.argmax(magnitudes)]
    frequency_resolution = sample_rate / frame_length

    assert abs(strongest_frequency - 440.0) <= frequency_resolution


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

