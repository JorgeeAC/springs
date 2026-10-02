"""Exact frame identity and time coordinates for precomputed analysis."""

from dataclasses import dataclass, field
from math import isfinite
from numbers import Integral, Real

import numpy as np


def _read_only(values: np.ndarray) -> np.ndarray:
    owned = np.array(values, copy=True)
    owned.setflags(write=False)
    return owned


def _require_integer(name: str, value: int, minimum: int) -> None:
    if isinstance(value, bool) or not isinstance(value, Integral) or value < minimum:
        qualifier = "non-negative" if minimum == 0 else f"at least {minimum}"
        raise ValueError(f"{name} must be an integer {qualifier}")


@dataclass(frozen=True)
class AnalysisTimeline:
    """Identify every complete analysis frame in one source signal.

    A frame's center is the midpoint of its first and last sample positions.
    For an even-length frame this lies halfway between two samples, which is
    why center times are floating-point values rather than sample indices.
    """

    source_sample_count: int
    sample_rate: int
    frame_length: int
    hop_length: int
    start_samples: np.ndarray = field(init=False, repr=False)
    end_samples_exclusive: np.ndarray = field(init=False, repr=False)
    center_samples: np.ndarray = field(init=False, repr=False)
    center_times_seconds: np.ndarray = field(init=False, repr=False)

    def __post_init__(self) -> None:
        _require_integer("source_sample_count", self.source_sample_count, 0)
        _require_integer("sample_rate", self.sample_rate, 1)
        _require_integer("frame_length", self.frame_length, 3)
        _require_integer("hop_length", self.hop_length, 1)
        if self.source_sample_count < self.frame_length:
            raise ValueError("source must contain at least one complete frame")

        frame_count = (
            1 + (self.source_sample_count - self.frame_length) // self.hop_length
        )
        start_samples = np.arange(frame_count, dtype=np.int64) * self.hop_length
        center_samples = (
            start_samples.astype(np.float64) + (self.frame_length - 1) / 2
        )
        center_times_seconds = center_samples / self.sample_rate
        object.__setattr__(self, "start_samples", _read_only(start_samples))
        object.__setattr__(
            self,
            "end_samples_exclusive",
            _read_only(start_samples + self.frame_length),
        )
        object.__setattr__(self, "center_samples", _read_only(center_samples))
        object.__setattr__(
            self,
            "center_times_seconds",
            _read_only(center_times_seconds),
        )

    @property
    def frame_count(self) -> int:
        return len(self.start_samples)

    @property
    def start_times_seconds(self) -> np.ndarray:
        """Return the time of each frame's first sample."""
        return _read_only(self.start_samples / self.sample_rate)

    @property
    def source_duration_seconds(self) -> float:
        return self.source_sample_count / self.sample_rate

    def nearest_frame_index(self, playback_time_seconds: float) -> int:
        """Return the frame whose center is nearest a source playback time.

        Times before the first or after the last center select the closest end
        frame. Exact ties select the earlier frame.
        """
        if not isfinite(playback_time_seconds):
            raise ValueError("playback_time_seconds must be finite")
        if not 0 <= playback_time_seconds <= self.source_duration_seconds:
            raise ValueError(
                "playback_time_seconds must be within the source duration "
                f"[0, {self.source_duration_seconds:g}]"
            )

        return self.nearest_frame_index_for_sample(
            playback_time_seconds * self.sample_rate
        )

    def nearest_frame_index_for_sample(self, playback_sample: float) -> int:
        """Return the frame nearest a source sample-position coordinate."""
        if (
            isinstance(playback_sample, bool)
            or not isinstance(playback_sample, Real)
            or not isfinite(playback_sample)
        ):
            raise ValueError("playback_sample must be a finite real number")
        if not 0 <= playback_sample <= self.source_sample_count:
            raise ValueError(
                "playback_sample must be within the source range "
                f"[0, {self.source_sample_count}]"
            )

        insertion = int(
            np.searchsorted(self.center_samples, playback_sample, side="left")
        )
        if insertion == 0:
            return 0
        if insertion == self.frame_count:
            return self.frame_count - 1

        previous_distance = playback_sample - self.center_samples[insertion - 1]
        next_distance = self.center_samples[insertion] - playback_sample
        if previous_distance <= next_distance:
            return insertion - 1
        return insertion
