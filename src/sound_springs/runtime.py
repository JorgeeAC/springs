"""Playback-clock synchronization for the existing spring simulation."""

from __future__ import annotations

from dataclasses import dataclass

from sound_springs.pipeline import FrameMeasurement, PipelineResult
from sound_springs.spring import Spring


@dataclass(frozen=True)
class RuntimeFrameState:
    """Values selected or simulated for one rendered runtime frame."""

    playback_time_seconds: float
    measurement: FrameMeasurement
    force: float
    spring_rest_position: float
    spring_position: float
    spring_velocity: float


class PlaybackSynchronizedSpring:
    """Advance a spring in fixed analysis-hop steps up to playback time.

    Rendering can occur faster or slower than analysis. Each mapped force is
    applied exactly once using the pipeline's hop duration. A backward clock
    jump resets and deterministically replays from the initial spring state.
    """

    def __init__(
        self,
        result: PipelineResult,
        spring: Spring | None = None,
    ) -> None:
        self._result = result
        initial = Spring() if spring is None else spring
        self._initial_parameters = {
            "position": initial.position,
            "velocity": initial.velocity,
            "mass": initial.mass,
            "stiffness": initial.stiffness,
            "damping": initial.damping,
            "rest_position": initial.rest_position,
        }
        self._spring = self._new_spring()
        self._simulated_through_frame_index = -1

    @property
    def spring(self) -> Spring:
        return self._spring

    @property
    def simulated_through_frame_index(self) -> int:
        return self._simulated_through_frame_index

    def _new_spring(self) -> Spring:
        return Spring(**self._initial_parameters)

    def reset(self) -> None:
        self._spring = self._new_spring()
        self._simulated_through_frame_index = -1

    def advance_to(self, playback_time_seconds: float) -> RuntimeFrameState:
        """Select the nearest measurement and catch simulation up to it."""
        measurement = self._result.measurement_at_time(playback_time_seconds)
        target_index = measurement.frame_index
        if target_index < self._simulated_through_frame_index:
            self.reset()

        for frame_index in range(
            self._simulated_through_frame_index + 1,
            target_index + 1,
        ):
            self._spring.update(
                force=float(self._result.forces[frame_index]),
                dt=self._result.timestep_seconds,
            )

        self._simulated_through_frame_index = target_index
        return RuntimeFrameState(
            playback_time_seconds=playback_time_seconds,
            measurement=measurement,
            force=float(self._result.forces[target_index]),
            spring_rest_position=self._spring.rest_position,
            spring_position=self._spring.position,
            spring_velocity=self._spring.velocity,
        )
