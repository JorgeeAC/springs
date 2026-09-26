"""Explicit framing and Fourier-transform calculations."""

import numpy as np


def frame_signal(
    signal: np.ndarray,
    frame_length: int = 2048,
    hop_length: int = 512,
) -> np.ndarray:
    """Split a one-dimensional signal into overlapping, complete frames.

    Incomplete frames at the end of the signal are not included.
    """
    if signal.ndim != 1:
        raise ValueError("signal must be one-dimensional")
    if frame_length <= 0:
        raise ValueError("frame_length must be positive")
    if hop_length <= 0:
        raise ValueError("hop_length must be positive")

    starts = range(0, len(signal) - frame_length + 1, hop_length)
    frames = [signal[start : start + frame_length] for start in starts]

    if not frames:
        return np.empty((0, frame_length), dtype=signal.dtype)
    return np.stack(frames)


def analyze_frame(frame: np.ndarray, sample_rate: int) -> tuple[np.ndarray, np.ndarray]:
    """Return the FFT-bin frequencies and magnitudes for one windowed frame."""
    if frame.ndim != 1:
        raise ValueError("frame must be one-dimensional")
    if len(frame) == 0:
        raise ValueError("frame must not be empty")
    if sample_rate <= 0:
        raise ValueError("sample_rate must be positive")

    # Taper the frame so its endpoints meet smoothly before the FFT.
    window = np.hanning(len(frame))
    windowed_frame = frame * window

    # A real-valued input has a mirrored spectrum, so rfft keeps only the
    # non-negative-frequency half. Magnitude discards the complex phase.
    spectrum = np.fft.rfft(windowed_frame)
    magnitudes = np.abs(spectrum)
    frequencies = np.fft.rfftfreq(len(frame), d=1 / sample_rate)
    return frequencies, magnitudes

