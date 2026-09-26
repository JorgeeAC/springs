"""Run the complete audio-spectrum-to-spring demonstration."""

import matplotlib.pyplot as plt
import numpy as np

from sound_springs.signal import generate_sine
from sound_springs.spectrum import analyze_frame, frame_signal
from sound_springs.spring import Spring


def main() -> None:
    sample_rate = 44_100
    duration_seconds = 2.0
    target_frequency_hz = 440.0
    frame_length = 2048
    hop_length = 512

    signal = generate_sine(target_frequency_hz, duration_seconds, sample_rate)
    frames = frame_signal(signal, frame_length, hop_length)

    target_magnitudes: list[float] = []
    frequencies: np.ndarray | None = None
    representative_magnitudes: np.ndarray | None = None
    representative_index = len(frames) // 2
    target_bin_index = 0

    for frame_index, frame in enumerate(frames):
        frequencies, magnitudes = analyze_frame(frame, sample_rate)
        target_bin_index = int(np.argmin(np.abs(frequencies - target_frequency_hz)))
        target_magnitudes.append(float(magnitudes[target_bin_index]))

        if frame_index == representative_index:
            representative_magnitudes = magnitudes

    # Scale the strongest observed magnitude to a force of 1.0. This preserves
    # the shape over time without introducing an arbitrary large force.
    peak_magnitude = max(target_magnitudes)
    forces = np.asarray(target_magnitudes) / peak_magnitude

    spring = Spring()
    dt = hop_length / sample_rate
    spring_positions: list[float] = []
    for force in forces:
        spring.update(force=float(force), dt=dt)
        spring_positions.append(spring.position)

    # These values are always assigned because a two-second signal contains
    # many complete frames.
    assert frequencies is not None
    assert representative_magnitudes is not None

    strongest_bin_index = int(np.argmax(representative_magnitudes))
    print(f"Sample rate: {sample_rate} Hz")
    print(f"Total sample count: {len(signal)}")
    print(f"Number of frames: {len(frames)}")
    print(
        f"FFT bin nearest 440 Hz: {target_bin_index} "
        f"({frequencies[target_bin_index]:.2f} Hz)"
    )
    print(
        "Strongest detected frequency in representative frame: "
        f"{frequencies[strongest_bin_index]:.2f} Hz"
    )

    figure, axes = plt.subplots(3, 1, figsize=(10, 9))

    waveform_sample_count = int(0.02 * sample_rate)
    waveform_time = np.arange(waveform_sample_count) / sample_rate
    axes[0].plot(waveform_time, signal[:waveform_sample_count])
    axes[0].set(title="First 20 ms of generated signal", xlabel="Time (s)", ylabel="Amplitude")

    axes[1].plot(frequencies, representative_magnitudes)
    axes[1].set(
        title="Magnitude spectrum of a representative frame",
        xlabel="Frequency (Hz)",
        ylabel="Magnitude",
        xlim=(0, 1_000),
    )

    spring_time = np.arange(len(spring_positions)) * dt
    axes[2].plot(spring_time, spring_positions)
    axes[2].set(title="Damped spring response", xlabel="Time (s)", ylabel="Position")

    figure.tight_layout()
    plt.show()


if __name__ == "__main__":
    main()

