"""Small pygame-backed music playback clock for the interactive runtime."""

from __future__ import annotations

from dataclasses import dataclass
from math import isfinite
from numbers import Integral
from pathlib import Path
from typing import Protocol

import pygame


DEFAULT_AUDIO_BUFFER_SAMPLES = 4_096


@dataclass(frozen=True)
class AudioOutputSettings:
    """Requested SDL mixer format and buffering for one source file."""

    sample_rate: int
    source_channel_count: int
    buffer_samples: int = DEFAULT_AUDIO_BUFFER_SAMPLES

    def __post_init__(self) -> None:
        if (
            isinstance(self.sample_rate, bool)
            or not isinstance(self.sample_rate, Integral)
            or self.sample_rate <= 0
        ):
            raise ValueError("sample_rate must be a positive integer")
        if (
            isinstance(self.source_channel_count, bool)
            or not isinstance(self.source_channel_count, Integral)
            or self.source_channel_count <= 0
        ):
            raise ValueError("source_channel_count must be a positive integer")
        if (
            isinstance(self.buffer_samples, bool)
            or not isinstance(self.buffer_samples, Integral)
            or self.buffer_samples <= 0
            or self.buffer_samples & (self.buffer_samples - 1)
        ):
            raise ValueError("buffer_samples must be a positive power of two")

    @property
    def output_channel_count(self) -> int:
        """SDL_mixer supports mono or stereo output."""
        return min(int(self.source_channel_count), 2)

    @property
    def buffer_milliseconds(self) -> float:
        return self.buffer_samples / self.sample_rate * 1_000


@dataclass(frozen=True)
class AudioBackendInfo:
    """Actual pygame/SDL audio configuration used by this process."""

    driver: str
    mixer_frequency_hz: int
    mixer_sample_size_bits: int
    mixer_channel_count: int
    buffer_samples: int
    buffer_milliseconds: float


def initialize_audio_output(settings: AudioOutputSettings) -> AudioBackendInfo:
    """Initialize SDL_mixer explicitly for faithful, dropout-resistant playback.

    The source file itself is streamed by SDL_mixer. Sound Springs never passes
    its decoded analysis array into this output path.
    """
    pygame.mixer.init(
        frequency=int(settings.sample_rate),
        size=-16,
        channels=settings.output_channel_count,
        buffer=int(settings.buffer_samples),
        allowedchanges=0,
    )
    negotiated = pygame.mixer.get_init()
    if negotiated is None:
        raise RuntimeError("pygame could not initialize an audio output device")
    frequency, sample_size, channels = negotiated
    return AudioBackendInfo(
        driver=pygame.mixer.get_driver(),
        mixer_frequency_hz=int(frequency),
        mixer_sample_size_bits=int(sample_size),
        mixer_channel_count=int(channels),
        buffer_samples=int(settings.buffer_samples),
        buffer_milliseconds=settings.buffer_milliseconds,
    )


class _MusicStream(Protocol):
    def load(self, filename: str) -> None: ...

    def play(self) -> None: ...

    def pause(self) -> None: ...

    def unpause(self) -> None: ...

    def stop(self) -> None: ...

    def unload(self) -> None: ...

    def get_pos(self) -> int: ...

    def get_busy(self) -> bool: ...


class MusicPlayback:
    """Play one file and expose SDL_mixer's elapsed playback time.

    ``pygame.mixer.music.get_pos`` reports elapsed playback milliseconds, not a
    device sample cursor. This first runtime starts only at the beginning, so
    the elapsed value is also the source playback position. Seeking is omitted
    because SDL_mixer does not support positioning WAV streams consistently.
    """

    def __init__(
        self,
        audio_file: str | Path,
        duration_seconds: float,
        *,
        music_stream: _MusicStream | None = None,
    ) -> None:
        if not isfinite(duration_seconds) or duration_seconds <= 0:
            raise ValueError("duration_seconds must be finite and positive")
        if music_stream is None and pygame.mixer.get_init() is None:
            raise RuntimeError("pygame mixer must be initialized before playback")

        self._music = pygame.mixer.music if music_stream is None else music_stream
        self._duration_seconds = duration_seconds
        self._started = False
        self._paused = False
        self._closed = False
        self._last_position_seconds = 0.0
        self._music.load(str(audio_file))

    @property
    def duration_seconds(self) -> float:
        return self._duration_seconds

    @property
    def is_paused(self) -> bool:
        return self._paused

    @property
    def is_finished(self) -> bool:
        return self._started and not self._paused and not self._music.get_busy()

    @property
    def position_seconds(self) -> float:
        """Return a monotonic, duration-clamped source position."""
        elapsed_milliseconds = self._music.get_pos()
        if elapsed_milliseconds >= 0:
            observed = min(
                elapsed_milliseconds / 1_000.0,
                self._duration_seconds,
            )
            self._last_position_seconds = max(
                self._last_position_seconds,
                observed,
            )
        elif self.is_finished:
            self._last_position_seconds = self._duration_seconds
        return self._last_position_seconds

    def play(self) -> None:
        if self._closed:
            raise RuntimeError("playback is closed")
        self._music.play()
        self._started = True
        self._paused = False
        self._last_position_seconds = 0.0

    def pause(self) -> None:
        if self._started and not self._paused and not self.is_finished:
            self._music.pause()
            self._paused = True

    def resume(self) -> None:
        if self._started and self._paused:
            self._music.unpause()
            self._paused = False

    def toggle_pause(self) -> None:
        if self._paused:
            self.resume()
        else:
            self.pause()

    def close(self) -> None:
        if not self._closed:
            self._music.stop()
            self._music.unload()
            self._closed = True
            self._paused = False

    def __enter__(self) -> MusicPlayback:
        return self

    def __exit__(self, *_exc_info: object) -> None:
        self.close()
