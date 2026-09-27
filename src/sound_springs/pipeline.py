"""Deterministic measurement, mapping, and simulation orchestration."""

from dataclasses import dataclass

import numpy as np

from sound_springs.mapping import peak_normalized_forces
from sound_springs.spectrum import analyze_frame
from sound_springs.spring import Spring


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
        if self.frame_length < 3:
            raise ValueError("frame_length must be at least 3")
        if self.hop_length <= 0:
            raise ValueError("hop_length must be positive")
        if not np.isfinite(self.target_frequency_hz) or self.target_frequency_hz < 0:
            raise ValueError("target_frequency_hz must be finite and non-negative")


@dataclass(frozen=True)
class PipelineResult:
    """Calculated data consumed by diagnostics or future renderers."""

    sample_rate: int
    settings: AnalysisSettings
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
        return np.arange(len(self.target_amplitudes)) * self.timestep_seconds

    @property
    def measured_frequency_hz(self) -> float:
        return float(self.frequencies[self.target_bin_index])


def run_pipeline(
    signal: np.ndarray,
    sample_rate: int,
    settings: AnalysisSettings = AnalysisSettings(),
) -> PipelineResult:
    """Measure one frequency, map it to force, and simulate one spring."""
    if sample_rate <= 0:
        raise ValueError("sample_rate must be positive")
    if settings.target_frequency_hz > sample_rate / 2:
        raise ValueError(
            "target_frequency_hz must not exceed the Nyquist frequency "
            f"({sample_rate / 2:g} Hz)"
        )

    if signal.ndim != 1:
        raise ValueError("signal must be one-dimensional")
    if len(signal) < settings.frame_length:
        raise ValueError(
            f"signal has {len(signal)} samples but frame_length is "
            f"{settings.frame_length}; at least one complete frame is required"
        )

    frame_count = 1 + (len(signal) - settings.frame_length) // settings.hop_length
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
    for frame_index in range(frame_count):
        if frame_index == 0:
            amplitudes = first_amplitudes
        else:
            start = frame_index * settings.hop_length
            frame = signal[start : start + settings.frame_length]
            _, amplitudes = analyze_frame(frame, sample_rate)
        target_amplitudes[frame_index] = amplitudes[target_bin_index]
        if frame_index == representative_frame_index:
            representative_amplitudes = amplitudes

    forces = peak_normalized_forces(target_amplitudes)
    spring = Spring()
    spring_positions = np.empty(len(forces), dtype=np.float64)
    timestep_seconds = settings.hop_length / sample_rate
    for index, force in enumerate(forces):
        spring.update(force=float(force), dt=timestep_seconds)
        spring_positions[index] = spring.position

    return PipelineResult(
        sample_rate=sample_rate,
        settings=settings,
        frequencies=_read_only(frequencies),
        representative_amplitudes=_read_only(representative_amplitudes),
        representative_frame_index=representative_frame_index,
        target_bin_index=target_bin_index,
        target_amplitudes=_read_only(target_amplitudes),
        forces=_read_only(forces),
        spring_positions=_read_only(spring_positions),
    )
