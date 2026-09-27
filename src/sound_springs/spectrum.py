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
    """Return frequencies and one-sided amplitudes for one Hann-windowed frame.

    Dividing by the Hann window's coherent gain makes a bin-centered sinusoid's
    measured amplitude comparable across supported frame lengths. Interior
    bins are doubled because ``rfft`` omits their negative-frequency mirrors;
    DC and the even-length Nyquist bin are not doubled.
    """
    if frame.ndim != 1:
        raise ValueError("frame must be one-dimensional")
    if len(frame) < 3:
        raise ValueError("frame must contain at least 3 samples")
    if sample_rate <= 0:
        raise ValueError("sample_rate must be positive")
    if not np.issubdtype(frame.dtype, np.number):
        raise ValueError("frame must be numeric")
    if not np.all(np.isfinite(frame)):
        raise ValueError("frame must contain only finite values")

    # Taper the frame so its endpoints meet smoothly before the FFT.
    window = np.hanning(len(frame))
    windowed_frame = frame * window

    # A real-valued input has a mirrored spectrum, so rfft keeps only the
    # non-negative-frequency half. Magnitude discards the complex phase. The
    # sum of the window is its coherent amplitude gain for this frame.
    spectrum = np.fft.rfft(windowed_frame)
    amplitudes = np.abs(spectrum) / np.sum(window)
    if len(frame) % 2 == 0:
        amplitudes[1:-1] *= 2
    else:
        amplitudes[1:] *= 2
    frequencies = np.fft.rfftfreq(len(frame), d=1 / sample_rate)
    return frequencies, amplitudes


def analyze_frames(
    frames: np.ndarray,
    sample_rate: int,
) -> tuple[np.ndarray, np.ndarray]:
    """Analyze a two-dimensional collection of equally sized frames."""
    if frames.ndim != 2:
        raise ValueError("frames must have shape (frame_count, frame_length)")
    if len(frames) == 0:
        raise ValueError("frames must contain at least one frame")

    frequencies, first_amplitudes = analyze_frame(frames[0], sample_rate)
    amplitudes = np.empty((len(frames), len(first_amplitudes)), dtype=np.float64)
    amplitudes[0] = first_amplitudes
    for index, frame in enumerate(frames[1:], start=1):
        _, amplitudes[index] = analyze_frame(frame, sample_rate)
    return frequencies, amplitudes
