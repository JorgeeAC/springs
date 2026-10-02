import pytest

from sound_springs.spring import Spring


def test_spring_at_rest_with_zero_force_stays_at_rest() -> None:
    spring = Spring(position=2.0, rest_position=2.0)

    spring.update(force=0.0, dt=0.01)

    assert spring.position == pytest.approx(2.0)
    assert spring.velocity == pytest.approx(0.0)


def test_displaced_spring_moves_toward_equilibrium() -> None:
    spring = Spring(position=1.0, rest_position=0.0)

    spring.update(force=0.0, dt=0.01)

    assert spring.position < 1.0
    assert spring.velocity < 0.0


def test_invalid_mass_and_timestep_are_rejected() -> None:
    with pytest.raises(ValueError, match="mass"):
        Spring(mass=0.0)

    spring = Spring()
    with pytest.raises(ValueError, match="dt"):
        spring.update(force=0.0, dt=0.0)


def test_damping_removes_mechanical_energy() -> None:
    undamped = Spring(position=1.0, damping=0.0)
    damped = Spring(position=1.0, damping=2.0)

    for _ in range(2_000):
        undamped.update(force=0.0, dt=0.001)
        damped.update(force=0.0, dt=0.001)

    assert damped.mechanical_energy < undamped.mechanical_energy * 0.05


def test_non_finite_parameters_and_force_are_rejected() -> None:
    with pytest.raises(ValueError, match="damping.*finite"):
        Spring(damping=float("nan"))
    with pytest.raises(ValueError, match="force.*finite"):
        Spring().update(force=float("inf"), dt=0.01)
