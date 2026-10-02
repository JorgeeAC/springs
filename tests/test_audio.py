from pathlib import Path

import numpy as np
import pytest
import soundfile as sf

from sound_springs.audio import AudioBuffer, AudioDecodeError, load_audio_file
from sound_springs.signal import generate_sine
from sound_springs.spectrum import analyze_frame


@pytest.mark.parametrize("extension, format_name", [("wav", "WAV"), ("flac", "FLAC")])
def test_load_audio_file_preserves_rate_channels_and_pcm(
    tmp_path: Path,
    extension: str,
    format_name: str,
) -> None:
    sample_rate = 8_000
    expected = np.column_stack(
        (
            np.linspace(-0.75, 0.75, 64),
            np.linspace(0.5, -0.5, 64),
        )
    )
    path = tmp_path / f"stereo.{extension}"
    sf.write(path, expected, sample_rate, format=format_name, subtype="PCM_16")

    audio = load_audio_file(path)

    assert audio.sample_rate == sample_rate
    assert audio.frame_count == len(expected)
    assert audio.channel_count == 2
    assert audio.duration_seconds == pytest.approx(len(expected) / sample_rate)
    np.testing.assert_allclose(audio.samples, expected, atol=1 / 2**15)


@pytest.mark.parametrize("extension, format_name", [("wav", "WAV"), ("flac", "FLAC")])
def test_known_tone_survives_file_round_trip_and_analysis(
    tmp_path: Path,
    extension: str,
    format_name: str,
) -> None:
    sample_rate = 8_192
    frame_length = 1_024
    expected_frequency = 440.0
    expected_amplitude = 0.6
    signal = generate_sine(
        expected_frequency,
        frame_length / sample_rate,
        sample_rate,
        amplitude=expected_amplitude,
    )
    path = tmp_path / f"known-tone.{extension}"
    sf.write(path, signal, sample_rate, format=format_name, subtype="PCM_16")

    decoded = load_audio_file(path)
    decoded_again = load_audio_file(path)
    frequencies, amplitudes = analyze_frame(decoded.channel(0), decoded.sample_rate)
    strongest_bin = int(np.argmax(amplitudes))

    assert decoded.sample_rate == sample_rate
    np.testing.assert_array_equal(decoded_again.samples, decoded.samples)
    assert frequencies[strongest_bin] == pytest.approx(expected_frequency)
    assert amplitudes[strongest_bin] == pytest.approx(
        expected_amplitude,
        abs=2 / 2**15,
    )


def test_mono_file_keeps_an_explicit_channel_dimension(tmp_path: Path) -> None:
    path = tmp_path / "mono.wav"
    sf.write(path, np.array([0.0, 0.25, -0.25]), 8_000, subtype="PCM_16")

    audio = load_audio_file(path)

    assert audio.samples.shape == (3, 1)
    np.testing.assert_allclose(audio.channel(0), [0.0, 0.25, -0.25], atol=1 / 2**15)


def test_audio_buffer_owns_read_only_samples() -> None:
    source = np.array([[0.25], [-0.25]])

    audio = AudioBuffer(samples=source, sample_rate=48_000)
    source[0, 0] = 1.0

    assert audio.samples[0, 0] == pytest.approx(0.25)
    with pytest.raises(ValueError, match="read-only"):
        audio.samples[0, 0] = 0.0


def test_audio_buffer_rejects_invalid_shape_and_non_finite_samples() -> None:
    with pytest.raises(ValueError, match="shape"):
        AudioBuffer(samples=np.zeros(4), sample_rate=44_100)
    with pytest.raises(ValueError, match="finite"):
        AudioBuffer(samples=np.array([[np.nan]]), sample_rate=44_100)


def test_load_audio_file_reports_actionable_errors(tmp_path: Path) -> None:
    with pytest.raises(AudioDecodeError, match="unsupported audio extension"):
        load_audio_file(tmp_path / "track.mp3")
    with pytest.raises(FileNotFoundError, match="does not exist"):
        load_audio_file(tmp_path / "missing.wav")

    corrupt_path = tmp_path / "corrupt.flac"
    corrupt_path.write_bytes(b"not an audio file")
    with pytest.raises(AudioDecodeError, match="could not decode"):
        load_audio_file(corrupt_path)
