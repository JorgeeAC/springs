import numpy as np
import pytest

from sound_springs.signal import generate_sine
from sound_springs.spectrum import (
    analyze_frame,
    apply_hann_window,
    energy_from_rfft,
)


def _full_fft_energy(frame: np.ndarray) -> float:
    spectrum = np.fft.fft(frame)
    return float(np.sum(np.abs(spectrum) ** 2) / len(frame))


@pytest.mark.parametrize(
    "frame",
    [
        generate_sine(440.0, 1_024 / 8_192, 8_192),
        generate_sine(440.0, 1_024 / 8_192, 8_192, amplitude=0.6)
        + generate_sine(880.0, 1_024 / 8_192, 8_192, amplitude=0.2),
        np.random.default_rng(20260926).standard_normal(1_024),
    ],
    ids=["sine", "two-tones", "deterministic-arbitrary-signal"],
)
def test_parseval_holds_for_full_fft_of_windowed_frame(frame: np.ndarray) -> None:
    windowed = apply_hann_window(frame)

    time_domain_energy = float(np.sum(windowed**2))
    frequency_domain_energy = _full_fft_energy(windowed)

    assert frequency_domain_energy == pytest.approx(
        time_domain_energy,
        rel=1e-12,
        abs=1e-12,
    )


@pytest.mark.parametrize("frame_length", [1_023, 1_024])
def test_rfft_energy_reconstructs_windowed_time_energy(frame_length: int) -> None:
    frame = np.random.default_rng(17).standard_normal(frame_length)
    windowed = apply_hann_window(frame)

    reconstructed = energy_from_rfft(np.fft.rfft(windowed), frame_length)

    assert reconstructed == pytest.approx(
        float(np.sum(windowed**2)),
        rel=1e-12,
        abs=1e-12,
    )


def test_sine_amplitude_scales_spectrum_linearly_and_energy_quadratically() -> None:
    sample_rate = 8_192
    frame_length = 1_024
    amplitudes = (0.25, 0.5, 1.0)
    measured_peaks = []
    energies = []

    for amplitude in amplitudes:
        frame = generate_sine(
            440.0,
            frame_length / sample_rate,
            sample_rate,
            amplitude=amplitude,
        )
        _, spectrum_amplitudes = analyze_frame(frame, sample_rate)
        measured_peaks.append(float(np.max(spectrum_amplitudes)))
        energies.append(float(np.sum(apply_hann_window(frame) ** 2)))

    np.testing.assert_allclose(
        np.array(measured_peaks) / measured_peaks[-1],
        amplitudes,
        rtol=2e-6,
        atol=0.0,
    )
    np.testing.assert_allclose(
        np.square(measured_peaks) / measured_peaks[-1] ** 2,
        np.square(amplitudes),
        rtol=4e-6,
        atol=0.0,
    )
    np.testing.assert_allclose(
        np.array(energies) / energies[-1],
        np.square(amplitudes),
        rtol=1e-12,
        atol=0.0,
    )


def test_rfft_energy_rejects_a_mismatched_representation() -> None:
    with pytest.raises(ValueError, match="spectrum length"):
        energy_from_rfft(np.zeros(3), frame_length=8)
