from pathlib import Path

import pytest

from sound_springs.playback import (
    DEFAULT_AUDIO_BUFFER_SAMPLES,
    AudioOutputSettings,
    MusicPlayback,
    initialize_audio_output,
)


class FakeMusicStream:
    def __init__(self) -> None:
        self.loaded: str | None = None
        self.position_ms = -1
        self.busy = False
        self.paused = False
        self.closed = False

    def load(self, filename: str) -> None:
        self.loaded = filename

    def play(self) -> None:
        self.position_ms = 0
        self.busy = True

    def pause(self) -> None:
        self.busy = False
        self.paused = True

    def unpause(self) -> None:
        self.busy = True
        self.paused = False

    def stop(self) -> None:
        self.busy = False

    def unload(self) -> None:
        self.closed = True

    def get_pos(self) -> int:
        return self.position_ms

    def get_busy(self) -> bool:
        return self.busy


def test_playback_exposes_elapsed_position_and_pause_state() -> None:
    stream = FakeMusicStream()
    playback = MusicPlayback(
        Path("song.wav"),
        2.0,
        music_stream=stream,
    )

    playback.play()
    stream.position_ms = 1_250
    assert playback.position_seconds == pytest.approx(1.25)

    playback.pause()
    assert playback.is_paused
    assert not playback.is_finished
    playback.resume()
    assert not playback.is_paused

    playback.close()
    assert stream.closed


def test_playback_position_is_monotonic_clamped_and_finishes_at_duration() -> None:
    stream = FakeMusicStream()
    playback = MusicPlayback("song.wav", 2.0, music_stream=stream)
    playback.play()

    stream.position_ms = 2_500
    assert playback.position_seconds == 2.0
    stream.position_ms = 1_500
    assert playback.position_seconds == 2.0

    stream.position_ms = -1
    stream.busy = False
    assert playback.is_finished
    assert playback.position_seconds == 2.0


def test_playback_rejects_invalid_duration_and_use_after_close() -> None:
    stream = FakeMusicStream()
    with pytest.raises(ValueError, match="duration_seconds"):
        MusicPlayback("song.wav", 0.0, music_stream=stream)

    playback = MusicPlayback("song.wav", 1.0, music_stream=stream)
    playback.close()
    playback.close()
    with pytest.raises(RuntimeError, match="closed"):
        playback.play()


def test_audio_output_settings_make_buffering_and_format_explicit() -> None:
    settings = AudioOutputSettings(sample_rate=44_100, source_channel_count=2)

    assert settings.buffer_samples == DEFAULT_AUDIO_BUFFER_SAMPLES
    assert settings.output_channel_count == 2
    assert settings.buffer_milliseconds == pytest.approx(92.8798, rel=1e-5)
    assert AudioOutputSettings(44_100, 6).output_channel_count == 2


@pytest.mark.parametrize("buffer_samples", [0, 500, 1_000])
def test_audio_output_buffer_must_be_a_positive_power_of_two(
    buffer_samples: int,
) -> None:
    with pytest.raises(ValueError, match="power of two"):
        AudioOutputSettings(44_100, 2, buffer_samples)


def test_audio_output_initialization_requests_exact_source_format(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    observed: dict[str, int] = {}

    def fake_init(**options: int) -> None:
        observed.update(options)

    monkeypatch.setattr(
        "sound_springs.playback.pygame.mixer.init",
        fake_init,
    )
    monkeypatch.setattr(
        "sound_springs.playback.pygame.mixer.get_init",
        lambda: (44_100, -16, 2),
    )
    monkeypatch.setattr(
        "sound_springs.playback.pygame.mixer.get_driver",
        lambda: "test-driver",
    )

    info = initialize_audio_output(AudioOutputSettings(44_100, 2, 4_096))

    assert observed == {
        "frequency": 44_100,
        "size": -16,
        "channels": 2,
        "buffer": 4_096,
        "allowedchanges": 0,
    }
    assert info.driver == "test-driver"
    assert info.mixer_frequency_hz == 44_100
    assert info.mixer_sample_size_bits == -16
    assert info.mixer_channel_count == 2
    assert info.buffer_samples == 4_096
    assert info.buffer_milliseconds == pytest.approx(92.8798, rel=1e-5)
