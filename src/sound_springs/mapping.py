"""Explicit mappings from measured audio features to model inputs."""

import numpy as np


def peak_normalized_forces(
    measurements: np.ndarray,
    maximum_force: float = 1.0,
) -> np.ndarray:
    """Map non-negative measurements proportionally into a force range.

    This is an interpretation chosen by Sound Springs, not a DSP operation.
    A silent measurement sequence maps to zero force instead of dividing by
    zero. The sequence peak maps to ``maximum_force``.
    """
    values = np.asarray(measurements, dtype=np.float64)
    if values.ndim != 1:
        raise ValueError("measurements must be one-dimensional")
    if len(values) == 0:
        raise ValueError("measurements must not be empty")
    if not np.all(np.isfinite(values)):
        raise ValueError("measurements must contain only finite values")
    if np.any(values < 0):
        raise ValueError("measurements must be non-negative")
    if not np.isfinite(maximum_force) or maximum_force < 0:
        raise ValueError("maximum_force must be finite and non-negative")

    peak = float(np.max(values))
    if peak == 0.0:
        return np.zeros_like(values)
    return values * (maximum_force / peak)
