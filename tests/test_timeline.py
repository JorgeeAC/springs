import numpy as np
import pytest

from sound_springs.timeline import AnalysisTimeline


def test_timeline_records_exact_complete_frame_coordinates() -> None:
    timeline = AnalysisTimeline(
        source_sample_count=2_048 + 2 * 512 + 511,
        sample_rate=8_192,
        frame_length=2_048,
        hop_length=512,
    )

    np.testing.assert_array_equal(timeline.start_samples, [0, 512, 1_024])
    np.testing.assert_array_equal(
        timeline.end_samples_exclusive,
        [2_048, 2_560, 3_072],
    )
    np.testing.assert_allclose(timeline.center_samples, [1_023.5, 1_535.5, 2_047.5])
    np.testing.assert_allclose(
        timeline.center_times_seconds,
        [1_023.5 / 8_192, 1_535.5 / 8_192, 2_047.5 / 8_192],
    )
    assert timeline.frame_count == 3
    with pytest.raises(ValueError, match="read-only"):
        timeline.start_samples[0] = 1


def test_nearest_frame_lookup_is_clamped_to_centers_and_ties_go_earlier() -> None:
    timeline = AnalysisTimeline(
        source_sample_count=20,
        sample_rate=10,
        frame_length=4,
        hop_length=4,
    )

    assert timeline.nearest_frame_index(0.0) == 0
    assert timeline.nearest_frame_index(0.35) == 0
    assert timeline.nearest_frame_index(0.36) == 1
    assert timeline.nearest_frame_index(timeline.source_duration_seconds) == 4
    assert timeline.nearest_frame_index_for_sample(3.5) == 0
    assert timeline.nearest_frame_index_for_sample(3.6) == 1


@pytest.mark.parametrize("time", [-0.01, 2.01, float("nan")])
def test_frame_lookup_rejects_times_outside_the_source(time: float) -> None:
    timeline = AnalysisTimeline(20, 10, 4, 4)

    with pytest.raises(ValueError, match="playback_time_seconds"):
        timeline.nearest_frame_index(time)


def test_sample_lookup_rejects_positions_outside_the_source() -> None:
    timeline = AnalysisTimeline(20, 10, 4, 4)

    with pytest.raises(ValueError, match="playback_sample"):
        timeline.nearest_frame_index_for_sample(21)


def test_timeline_requires_a_complete_frame() -> None:
    with pytest.raises(ValueError, match="complete frame"):
        AnalysisTimeline(3, 8_000, 4, 2)


def test_timeline_rejects_non_integer_coordinates() -> None:
    with pytest.raises(ValueError, match="source_sample_count.*integer"):
        AnalysisTimeline(20.5, 8_000, 4, 2)  # type: ignore[arg-type]
