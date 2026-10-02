import numpy as np
import pytest

from sound_springs.audio import AudioBuffer
from sound_springs.demo import select_analysis_channel


def test_mono_input_uses_its_only_channel() -> None:
    audio = AudioBuffer.from_mono(np.zeros(8), sample_rate=8_000)

    assert select_analysis_channel(audio, None) == 0


def test_multichannel_input_requires_an_explicit_channel() -> None:
    audio = AudioBuffer(np.zeros((8, 2)), sample_rate=8_000)

    with pytest.raises(ValueError, match="choose one explicitly"):
        select_analysis_channel(audio, None)
    assert select_analysis_channel(audio, 1) == 1
    with pytest.raises(ValueError, match="out of range"):
        select_analysis_channel(audio, 2)
