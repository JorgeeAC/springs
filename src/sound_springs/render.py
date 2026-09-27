"""Diagnostic presentation of already-calculated pipeline data."""

import matplotlib.pyplot as plt
from matplotlib.figure import Figure
import numpy as np

from sound_springs.pipeline import PipelineResult


def create_diagnostic_figure(
    signal: np.ndarray,
    result: PipelineResult,
    *,
    source_label: str,
) -> Figure:
    """Plot source samples, one calculated spectrum, and spring positions."""
    figure, axes = plt.subplots(3, 1, figsize=(10, 9))

    waveform_sample_count = min(len(signal), int(0.02 * result.sample_rate))
    waveform_time = np.arange(waveform_sample_count) / result.sample_rate
    axes[0].plot(waveform_time, signal[:waveform_sample_count])
    axes[0].set(
        title=f"First 20 ms of {source_label}",
        xlabel="Time (s)",
        ylabel="Amplitude",
    )

    maximum_display_frequency = min(
        result.sample_rate / 2,
        max(1_000.0, result.settings.target_frequency_hz * 1.5),
    )
    axes[1].plot(result.frequencies, result.representative_amplitudes)
    axes[1].set(
        title="Amplitude spectrum of a representative frame",
        xlabel="Frequency (Hz)",
        ylabel="Amplitude",
        xlim=(0, maximum_display_frequency),
    )

    axes[2].plot(result.frame_times_seconds, result.spring_positions)
    axes[2].set(
        title="Damped spring response",
        xlabel="Time (s)",
        ylabel="Position",
    )

    figure.tight_layout()
    return figure
