"""Deterministic measurement, mapping, and simulation orchestration."""

from __future__ import annotations

from dataclasses import dataclass
from numbers import Integral
from typing import TYPE_CHECKING

import numpy as np

from sound_springs.mapping import peak_normalized_forces
from sound_springs.spectrum import analyze_frame
from sound_springs.spring import Spring
from sound_springs.timeline import AnalysisTimeline

if TYPE_CHECKING:
    from sound_springs.diagnostics import DiagnosticRun


def _read_only(values: np.ndarray) -> np.ndarray:
    owned = np.array(values, copy=True)
    owned.setflags(write=False)
    return owned


@dataclass(frozen=True)
class AnalysisSettings:
    """Parameters defining repeatable frame and target-bin measurements."""

    frame_length: int = 2_048
    hop_length: int = 512
    target_frequency_hz: float = 440.0

    def __post_init__(self) -> None:
        if (
            isinstance(self.frame_length, bool)
            or not isinstance(self.frame_length, Integral)
            or self.frame_length < 3
        ):
            raise ValueError("frame_length must be an integer at least 3")
        if (
            isinstance(self.hop_length, bool)
            or not isinstance(self.hop_length, Integral)
            or self.hop_length <= 0
        ):
            raise ValueError("hop_length must be a positive integer")
        if not np.isfinite(self.target_frequency_hz) or self.target_frequency_hz < 0:
            raise ValueError("target_frequency_hz must be finite and non-negative")


@dataclass(frozen=True)
class FrameMeasurement:
    """One measured feature attached to its exact source-frame identity."""

    frame_index: int
    start_sample: int
    end_sample_exclusive: int
    center_sample: float
    center_time_seconds: float
    frequency_bin_index: int
    frequency_hz: float
    target_amplitude: float


@dataclass(frozen=True)
class PipelineResult:
    """Calculated data consumed by diagnostics or future renderers."""

    sample_rate: int
    settings: AnalysisSettings
    timeline: AnalysisTimeline
    frequencies: np.ndarray
    representative_amplitudes: np.ndarray
    representative_frame_index: int
    target_bin_index: int
    target_amplitudes: np.ndarray
    forces: np.ndarray
    spring_positions: np.ndarray

    @property
    def timestep_seconds(self) -> float:
        return self.settings.hop_length / self.sample_rate

    @property
    def frame_times_seconds(self) -> np.ndarray:
        """Backward-compatible alias for frame-center measurement times."""
        return self.measurement_times_seconds

    @property
    def measurement_times_seconds(self) -> np.ndarray:
        """Return exact center times of measured source frames."""
        return self.timeline.center_times_seconds

    @property
    def simulation_times_seconds(self) -> np.ndarray:
        """Times of states after each force has advanced the simulation."""
        values = (np.arange(len(self.spring_positions)) + 1) * self.timestep_seconds
        return _read_only(values)

    @property
    def measured_frequency_hz(self) -> float:
        return float(self.frequencies[self.target_bin_index])

    def frame_index_at_time(self, playback_time_seconds: float) -> int:
        """Select a measurement deterministically by nearest frame center."""
        return self.timeline.nearest_frame_index(playback_time_seconds)

    def frame_index_at_sample(self, playback_sample: float) -> int:
        """Select a measurement by nearest frame-center sample coordinate."""
        return self.timeline.nearest_frame_index_for_sample(playback_sample)

    def measurement_at_time(self, playback_time_seconds: float) -> FrameMeasurement:
        """Return the nearest target-bin measurement with its frame identity."""
        frame_index = self.frame_index_at_time(playback_time_seconds)
        return self._measurement(frame_index)

    def measurement_at_sample(self, playback_sample: float) -> FrameMeasurement:
        """Return a target-bin measurement selected by source sample position."""
        frame_index = self.frame_index_at_sample(playback_sample)
        return self._measurement(frame_index)

    def _measurement(self, frame_index: int) -> FrameMeasurement:
        return FrameMeasurement(
            frame_index=frame_index,
            start_sample=int(self.timeline.start_samples[frame_index]),
            end_sample_exclusive=int(
                self.timeline.end_samples_exclusive[frame_index]
            ),
            center_sample=float(self.timeline.center_samples[frame_index]),
            center_time_seconds=float(
                self.timeline.center_times_seconds[frame_index]
            ),
            frequency_bin_index=self.target_bin_index,
            frequency_hz=self.measured_frequency_hz,
            target_amplitude=float(self.target_amplitudes[frame_index]),
        )


def run_pipeline(
    signal: np.ndarray,
    sample_rate: int,
    settings: AnalysisSettings = AnalysisSettings(),
    diagnostics: DiagnosticRun | None = None,
) -> PipelineResult:
    """Measure one frequency, map it to force, and simulate one spring."""
    signal = np.asarray(signal)
    if sample_rate <= 0:
        raise ValueError("sample_rate must be positive")
    if settings.target_frequency_hz > sample_rate / 2:
        raise ValueError(
            "target_frequency_hz must not exceed the Nyquist frequency "
            f"({sample_rate / 2:g} Hz)"
        )

    if signal.ndim != 1:
        raise ValueError("signal must be one-dimensional")
    if not np.issubdtype(signal.dtype, np.number) or np.issubdtype(
        signal.dtype, np.complexfloating
    ):
        raise ValueError("signal must be real-valued numeric data")
    if not np.all(np.isfinite(signal)):
        raise ValueError("signal must contain only finite values")
    if len(signal) < settings.frame_length:
        raise ValueError(
            f"signal has {len(signal)} samples but frame_length is "
            f"{settings.frame_length}; at least one complete frame is required"
        )

    if diagnostics is None:
        timeline = AnalysisTimeline(
            source_sample_count=len(signal),
            sample_rate=sample_rate,
            frame_length=settings.frame_length,
            hop_length=settings.hop_length,
        )
    else:
        with diagnostics.measure("timeline_s"):
            timeline = AnalysisTimeline(
                source_sample_count=len(signal),
                sample_rate=sample_rate,
                frame_length=settings.frame_length,
                hop_length=settings.hop_length,
            )
    frame_count = timeline.frame_count

    def analyze_frames() -> tuple[np.ndarray, np.ndarray, int, int, np.ndarray]:
        first_frame = signal[: settings.frame_length]
        frequencies, first_amplitudes = analyze_frame(first_frame, sample_rate)
        target_bin_index = int(
            np.argmin(np.abs(frequencies - settings.target_frequency_hz))
        )
        representative_frame_index = frame_count // 2
        representative_amplitudes = first_amplitudes
        target_amplitudes = np.empty(frame_count, dtype=np.float64)

        # Analyze slices of the source in place. Materializing every overlapping
        # frame would multiply memory use for a normal-length music file.
        for frame_index, start in enumerate(timeline.start_samples):
            if frame_index == 0:
                amplitudes = first_amplitudes
            else:
                frame = signal[start : start + settings.frame_length]
                _, amplitudes = analyze_frame(frame, sample_rate)
            target_amplitudes[frame_index] = amplitudes[target_bin_index]
            if frame_index == representative_frame_index:
                representative_amplitudes = amplitudes
        return (
            frequencies,
            representative_amplitudes,
            representative_frame_index,
            target_bin_index,
            target_amplitudes,
        )

    if diagnostics is None:
        analysis_values = analyze_frames()
    else:
        with diagnostics.measure("dsp_analysis_s"):
            analysis_values = analyze_frames()
    (
        frequencies,
        representative_amplitudes,
        representative_frame_index,
        target_bin_index,
        target_amplitudes,
    ) = analysis_values

    def map_and_simulate() -> tuple[np.ndarray, np.ndarray]:
        forces = peak_normalized_forces(target_amplitudes)
        spring = Spring()
        spring_positions = np.empty(len(forces), dtype=np.float64)
        timestep_seconds = settings.hop_length / sample_rate
        for index, force in enumerate(forces):
            spring.update(force=float(force), dt=timestep_seconds)
            spring_positions[index] = spring.position
        return forces, spring_positions

    if diagnostics is None:
        forces, spring_positions = map_and_simulate()
    else:
        with diagnostics.measure("mapping_simulation_s"):
            forces, spring_positions = map_and_simulate()

    return PipelineResult(
        sample_rate=sample_rate,
        settings=settings,
        timeline=timeline,
        frequencies=_read_only(frequencies),
        representative_amplitudes=_read_only(representative_amplitudes),
        representative_frame_index=representative_frame_index,
        target_bin_index=target_bin_index,
        target_amplitudes=_read_only(target_amplitudes),
        forces=_read_only(forces),
        spring_positions=_read_only(spring_positions),
    )
