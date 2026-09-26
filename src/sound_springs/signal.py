"""Functions for generating simple signals."""

import numpy as np


def generate_sine(
    frequency_hz: float,
    duration_seconds: float,
    sample_rate: int,
) -> np.ndarray:
    """Generate a sine wave with the requested frequency and duration."""
    if duration_seconds < 0:
        raise ValueError("duration_seconds must be non-negative")
    if sample_rate <= 0:
        raise ValueError("sample_rate must be positive")

    sample_count = int(duration_seconds * sample_rate)
    time = np.arange(sample_count) / sample_rate
    signal = np.sin(2 * np.pi * frequency_hz * time)
    return signal

