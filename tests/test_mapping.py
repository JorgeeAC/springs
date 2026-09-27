import numpy as np
import pytest

from sound_springs.mapping import peak_normalized_forces


def test_peak_normalized_forces_preserve_proportions() -> None:
    forces = peak_normalized_forces(np.array([0.25, 0.5, 1.0]), maximum_force=2.0)

    np.testing.assert_allclose(forces, [0.5, 1.0, 2.0])


def test_silence_maps_to_zero_force() -> None:
    np.testing.assert_array_equal(peak_normalized_forces(np.zeros(4)), 0.0)


@pytest.mark.parametrize(
    "measurements, error",
    [
        (np.array([-0.1, 0.2]), "non-negative"),
        (np.array([0.1, np.nan]), "finite"),
        (np.empty(0), "empty"),
    ],
)
def test_invalid_measurements_are_rejected(measurements: np.ndarray, error: str) -> None:
    with pytest.raises(ValueError, match=error):
        peak_normalized_forces(measurements)
