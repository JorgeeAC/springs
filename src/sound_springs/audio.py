"""Decode supported music files into a format-neutral PCM boundary."""

from dataclasses import dataclass
from pathlib import Path
from typing import Self

import numpy as np
import soundfile as sf


SUPPORTED_AUDIO_SUFFIXES = frozenset({".flac", ".wav"})


class AudioDecodeError(ValueError):
    """Raised when a supported audio file cannot be decoded."""


@dataclass(frozen=True)
class AudioBuffer:
    """Decoded floating-point PCM samples arranged as frames by channels.

    Keeping the channel dimension even for mono files gives downstream code
    one stable representation and avoids silently choosing a stereo policy.
    """

    samples: np.ndarray
    sample_rate: int

    def __post_init__(self) -> None:
        samples = np.asarray(self.samples)
        if samples.ndim != 2:
            raise ValueError("samples must have shape (frames, channels)")
        if samples.shape[1] == 0:
            raise ValueError("samples must contain at least one channel")
        if self.sample_rate <= 0:
            raise ValueError("sample_rate must be positive")
        if not np.issubdtype(samples.dtype, np.number) or np.issubdtype(
            samples.dtype, np.complexfloating
        ):
            raise ValueError("samples must be real-valued numeric data")
        if not np.all(np.isfinite(samples)):
            raise ValueError("samples must contain only finite values")

        # Own an immutable float64 copy so caller mutations cannot change an
        # already-decoded input or make repeated analysis non-deterministic.
        owned_samples = np.array(samples, dtype=np.float64, order="C", copy=True)
        owned_samples.setflags(write=False)
        object.__setattr__(self, "samples", owned_samples)

    @classmethod
    def from_mono(cls, samples: np.ndarray, sample_rate: int) -> Self:
        """Build a buffer from a one-dimensional controlled/test signal."""
        mono_samples = np.asarray(samples)
        if mono_samples.ndim != 1:
            raise ValueError("mono samples must be one-dimensional")
        return cls(samples=mono_samples[:, np.newaxis], sample_rate=sample_rate)

    @property
    def frame_count(self) -> int:
        """Number of sample frames in the decoded file."""
        return int(self.samples.shape[0])

    @property
    def channel_count(self) -> int:
        """Number of independent channels in each sample frame."""
        return int(self.samples.shape[1])

    @property
    def duration_seconds(self) -> float:
        """Decoded duration derived from frame count and sample rate."""
        return self.frame_count / self.sample_rate

    def channel(self, index: int) -> np.ndarray:
        """Return one channel without applying an implicit stereo policy."""
        if not 0 <= index < self.channel_count:
            raise IndexError(
                f"channel index {index} is out of range for "
                f"{self.channel_count} channel(s)"
            )
        return self.samples[:, index]


def select_analysis_channel(
    audio: AudioBuffer, requested_channel: int | None
) -> int:
    """Resolve a channel without silently defining a stereo mixdown policy."""
    if requested_channel is None:
        if audio.channel_count == 1:
            return 0
        raise ValueError(
            f"input has {audio.channel_count} channels; choose one explicitly "
            "with --channel (zero-based)"
        )
    if not 0 <= requested_channel < audio.channel_count:
        raise ValueError(
            f"channel {requested_channel} is out of range for "
            f"{audio.channel_count} channel(s)"
        )
    return requested_channel


def load_audio_file(path: str | Path) -> AudioBuffer:
    """Decode a WAV or FLAC file as float64 PCM sample frames.

    Integer PCM is normalized by libsndfile when it is converted to floating
    point. Floating-point audio is retained as stored and can exceed [-1, 1].
    """
    audio_path = Path(path)
    if audio_path.suffix.lower() not in SUPPORTED_AUDIO_SUFFIXES:
        supported = ", ".join(sorted(SUPPORTED_AUDIO_SUFFIXES))
        raise AudioDecodeError(
            f"unsupported audio extension {audio_path.suffix or '<none>'!r}; "
            f"expected one of: {supported}"
        )
    if not audio_path.exists():
        raise FileNotFoundError(f"audio file does not exist: {audio_path}")
    if not audio_path.is_file():
        raise AudioDecodeError(f"audio path is not a file: {audio_path}")

    try:
        samples, sample_rate = sf.read(
            audio_path,
            dtype="float64",
            always_2d=True,
        )
    except (OSError, sf.LibsndfileError) as error:
        raise AudioDecodeError(f"could not decode audio file {audio_path}: {error}") from error

    return AudioBuffer(samples=samples, sample_rate=int(sample_rate))
