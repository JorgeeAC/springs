"""Functions for generating simple signals."""

from math import isfinite

import numpy as np


def _validate_signal_parameters(duration_seconds: float, sample_rate: int) -> None:
    if not isfinite(duration_seconds) or duration_seconds < 0:
        raise ValueError("duration_seconds must be finite and non-negative")
    if sample_rate <= 0:
        raise ValueError("sample_rate must be positive")


def _validate_frequency(frequency_hz: float, sample_rate: int, name: str) -> None:
    if not isfinite(frequency_hz) or frequency_hz < 0:
        raise ValueError(f"{name} must be finite and non-negative")
    if frequency_hz > sample_rate / 2:
        raise ValueError(f"{name} must not exceed the Nyquist frequency")


def generate_sine(
    frequency_hz: float,
    duration_seconds: float,
    sample_rate: int,
) -> np.ndarray:
    """Generate a sine wave with the requested frequency and duration."""
    _validate_signal_parameters(duration_seconds, sample_rate)
    _validate_frequency(frequency_hz, sample_rate, "frequency_hz")

    sample_count = int(duration_seconds * sample_rate)
    time = np.arange(sample_count) / sample_rate
    signal = np.sin(2 * np.pi * frequency_hz * time)
    return signal


def generate_linear_chirp(
    start_frequency_hz: float,
    end_frequency_hz: float,
    duration_seconds: float,
    sample_rate: int,
) -> np.ndarray:
    """Generate a sine whose instantaneous frequency changes linearly."""
    _validate_signal_parameters(duration_seconds, sample_rate)
    _validate_frequency(start_frequency_hz, sample_rate, "start_frequency_hz")
    _validate_frequency(end_frequency_hz, sample_rate, "end_frequency_hz")

    sample_count = int(duration_seconds * sample_rate)
    if sample_count == 0:
        return np.empty(0, dtype=np.float64)

    time = np.arange(sample_count) / sample_rate
    sweep_rate = (end_frequency_hz - start_frequency_hz) / duration_seconds
    phase = 2 * np.pi * (
        start_frequency_hz * time + 0.5 * sweep_rate * time**2
    )
    return np.sin(phase)
