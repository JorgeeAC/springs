"""A minimal damped spring simulation."""

from dataclasses import dataclass
from math import isfinite


@dataclass
class Spring:
    """State and physical parameters for a one-dimensional damped spring."""

    position: float = 0.0
    velocity: float = 0.0
    mass: float = 1.0
    stiffness: float = 20.0
    damping: float = 2.0
    rest_position: float = 0.0

    def __post_init__(self) -> None:
        parameter_values = {
            "position": self.position,
            "velocity": self.velocity,
            "mass": self.mass,
            "stiffness": self.stiffness,
            "damping": self.damping,
            "rest_position": self.rest_position,
        }
        for name, value in parameter_values.items():
            if not isfinite(value):
                raise ValueError(f"{name} must be finite")
        if self.mass <= 0:
            raise ValueError("mass must be positive")
        if self.stiffness < 0:
            raise ValueError("stiffness must be non-negative")
        if self.damping < 0:
            raise ValueError("damping must be non-negative")

    def update(self, force: float, dt: float) -> None:
        """Advance the spring by one semi-implicit Euler step."""
        if not isfinite(force):
            raise ValueError("force must be finite")
        if not isfinite(dt) or dt <= 0:
            raise ValueError("dt must be finite and positive")

        # Newton's second law: external force minus damping and spring forces.
        acceleration = (
            force
            - self.damping * self.velocity
            - self.stiffness * (self.position - self.rest_position)
        ) / self.mass

        # Semi-implicit Euler uses the new velocity to update the position.
        self.velocity += acceleration * dt
        self.position += self.velocity * dt

    @property
    def mechanical_energy(self) -> float:
        """Return kinetic plus spring potential energy (excluding forcing)."""
        displacement = self.position - self.rest_position
        return (
            0.5 * self.mass * self.velocity**2
            + 0.5 * self.stiffness * displacement**2
        )
