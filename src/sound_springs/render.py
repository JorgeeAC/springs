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

    representative_index = result.representative_frame_index
    representative_start = int(result.timeline.start_samples[representative_index])
    representative_end = int(
        result.timeline.end_samples_exclusive[representative_index]
    )
    representative_center = result.timeline.center_times_seconds[representative_index]
    waveform_time = (
        np.arange(representative_start, representative_end) / result.sample_rate
    )
    axes[0].plot(waveform_time, signal[representative_start:representative_end])
    axes[0].set(
        title=(
            f"Waveform of {source_label} — frame {representative_index} — "
            f"samples [{representative_start}, {representative_end})"
        ),
        xlabel="Time (s)",
        ylabel="Amplitude",
    )

    maximum_display_frequency = min(
        result.sample_rate / 2,
        max(1_000.0, result.settings.target_frequency_hz * 1.5),
    )
    axes[1].plot(result.frequencies, result.representative_amplitudes)
    axes[1].set(
        title=(
            f"Amplitude spectrum — frame {representative_index} — "
            f"samples [{representative_start}, {representative_end}) — "
            f"center {representative_center:.6f} s"
        ),
        xlabel="Frequency (Hz)",
        ylabel="Amplitude",
        xlim=(0, maximum_display_frequency),
    )

    axes[2].plot(result.simulation_times_seconds, result.spring_positions)
    axes[2].set(
        title="Damped spring response",
        xlabel="Simulation time after initial state (s)",
        ylabel="Position",
    )

    figure.tight_layout()
    return figure
