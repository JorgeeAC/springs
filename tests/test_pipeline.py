import numpy as np
import pytest

from sound_springs.diagnostics import DiagnosticRun
from sound_springs.pipeline import AnalysisSettings, run_pipeline
from sound_springs.signal import generate_sine


def test_pipeline_results_are_repeatable_and_read_only() -> None:
    sample_rate = 8_192
    signal = generate_sine(440.0, 0.5, sample_rate)
    settings = AnalysisSettings(frame_length=1_024, hop_length=256)

    first = run_pipeline(signal, sample_rate, settings)
    second = run_pipeline(signal, sample_rate, settings)

    np.testing.assert_array_equal(first.target_amplitudes, second.target_amplitudes)
    np.testing.assert_array_equal(first.forces, second.forces)
    np.testing.assert_array_equal(first.spring_positions, second.spring_positions)
    assert first.measured_frequency_hz == pytest.approx(440.0)
    np.testing.assert_array_equal(
        first.timeline.start_samples,
        np.arange(len(first.target_amplitudes)) * settings.hop_length,
    )
    assert first.frame_index_at_time(first.measurement_times_seconds[2]) == 2
    measurement = first.measurement_at_time(first.measurement_times_seconds[2])
    assert first.measurement_at_sample(measurement.center_sample) == measurement
    assert measurement.frame_index == 2
    assert measurement.start_sample == 2 * settings.hop_length
    assert measurement.end_sample_exclusive == (
        measurement.start_sample + settings.frame_length
    )
    assert measurement.center_sample == pytest.approx(
        measurement.start_sample + (settings.frame_length - 1) / 2
    )
    assert measurement.frequency_bin_index == first.target_bin_index
    assert measurement.frequency_hz == first.measured_frequency_hz
    assert measurement.target_amplitude == first.target_amplitudes[2]
    with pytest.raises(ValueError, match="read-only"):
        first.forces[0] = 10.0


def test_diagnostics_do_not_change_deterministic_pipeline_results() -> None:
    sample_rate = 8_192
    signal = generate_sine(440.0, 0.5, sample_rate)
    settings = AnalysisSettings(frame_length=1_024, hop_length=256)
    diagnostics = DiagnosticRun(run_id="pipeline-test")

    expected = run_pipeline(signal, sample_rate, settings)
    observed = run_pipeline(signal, sample_rate, settings, diagnostics=diagnostics)

    assert observed.sample_rate == expected.sample_rate
    assert observed.settings == expected.settings
    assert (
        observed.representative_frame_index
        == expected.representative_frame_index
    )
    assert observed.target_bin_index == expected.target_bin_index
    for field_name in (
        "start_samples",
        "end_samples_exclusive",
        "center_samples",
        "center_times_seconds",
    ):
        np.testing.assert_array_equal(
            getattr(observed.timeline, field_name),
            getattr(expected.timeline, field_name),
        )
    np.testing.assert_array_equal(observed.frequencies, expected.frequencies)
    np.testing.assert_array_equal(
        observed.representative_amplitudes,
        expected.representative_amplitudes,
    )
    np.testing.assert_array_equal(
        observed.target_amplitudes, expected.target_amplitudes
    )
    np.testing.assert_array_equal(observed.forces, expected.forces)
    np.testing.assert_array_equal(observed.spring_positions, expected.spring_positions)
    assert diagnostics.metrics["timeline_s"] >= 0
    assert diagnostics.metrics["dsp_analysis_s"] >= 0
    assert diagnostics.metrics["mapping_simulation_s"] >= 0


def test_measurement_and_simulation_times_have_explicit_distinct_meanings() -> None:
    sample_rate = 8_000
    settings = AnalysisSettings(frame_length=400, hop_length=80)
    result = run_pipeline(np.zeros(800), sample_rate, settings)

    assert result.measurement_times_seconds[0] == pytest.approx(199.5 / sample_rate)
    assert result.simulation_times_seconds[0] == pytest.approx(80 / sample_rate)
    assert result.simulation_times_seconds[-1] == pytest.approx(
        len(result.spring_positions) * 80 / sample_rate
    )


def test_silence_produces_no_force_or_spring_motion() -> None:
    result = run_pipeline(
        np.zeros(2_048),
        8_192,
        AnalysisSettings(frame_length=512, hop_length=128),
    )

    np.testing.assert_array_equal(result.target_amplitudes, 0.0)
    np.testing.assert_array_equal(result.forces, 0.0)
    np.testing.assert_array_equal(result.spring_positions, 0.0)


def test_pipeline_rejects_too_short_signal_and_frequency_above_nyquist() -> None:
    with pytest.raises(ValueError, match="complete frame"):
        run_pipeline(np.zeros(100), 44_100)
    with pytest.raises(ValueError, match="Nyquist"):
        run_pipeline(
            np.zeros(2_048),
            8_000,
            AnalysisSettings(target_frequency_hz=4_001.0),
        )
    with pytest.raises(ValueError, match="frame_length.*integer"):
        AnalysisSettings(frame_length=512.5)  # type: ignore[arg-type]
    signal_with_non_finite_dropped_tail = np.zeros(2_049)
    signal_with_non_finite_dropped_tail[-1] = np.nan
    with pytest.raises(ValueError, match="finite"):
        run_pipeline(signal_with_non_finite_dropped_tail, 8_192)
