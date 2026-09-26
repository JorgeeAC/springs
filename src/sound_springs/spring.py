"""A minimal damped spring simulation."""

from dataclasses import dataclass


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
        if self.mass <= 0:
            raise ValueError("mass must be positive")
        if self.stiffness < 0:
            raise ValueError("stiffness must be non-negative")
        if self.damping < 0:
            raise ValueError("damping must be non-negative")

    def update(self, force: float, dt: float) -> None:
        """Advance the spring by one semi-implicit Euler step."""
        if dt <= 0:
            raise ValueError("dt must be positive")

        # Newton's second law: external force minus damping and spring forces.
        acceleration = (
            force
            - self.damping * self.velocity
            - self.stiffness * (self.position - self.rest_position)
        ) / self.mass

        # Semi-implicit Euler uses the new velocity to update the position.
        self.velocity += acceleration * dt
        self.position += self.velocity * dt

