import matplotlib
import numpy as np
import pytest

matplotlib.use("Agg")

from matplotlib import pyplot as plt  # noqa: E402

from sound_springs.pipeline import AnalysisSettings, run_pipeline  # noqa: E402
from sound_springs.render import create_diagnostic_figure  # noqa: E402


def test_waveform_and_spectrum_identify_the_same_representative_frame() -> None:
    sample_rate = 8_000
    signal = np.arange(800, dtype=np.float64)
    result = run_pipeline(
        signal,
        sample_rate,
        AnalysisSettings(frame_length=200, hop_length=100),
    )

    figure = create_diagnostic_figure(signal, result, source_label="fixture.wav")
    try:
        frame_index = result.representative_frame_index
        start = int(result.timeline.start_samples[frame_index])
        end = int(result.timeline.end_samples_exclusive[frame_index])
        waveform_x = figure.axes[0].lines[0].get_xdata()

        assert waveform_x[0] == pytest.approx(start / sample_rate)
        assert waveform_x[-1] == pytest.approx((end - 1) / sample_rate)
        assert f"frame {frame_index}" in figure.axes[0].get_title()
        assert f"frame {frame_index}" in figure.axes[1].get_title()
        assert f"samples [{start}, {end})" in figure.axes[0].get_title()
        assert f"samples [{start}, {end})" in figure.axes[1].get_title()
    finally:
        plt.close(figure)
