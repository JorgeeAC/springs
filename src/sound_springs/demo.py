"""Run the music-file-to-spring diagnostic application."""

import argparse
from collections.abc import Sequence
from pathlib import Path

import matplotlib.pyplot as plt

from sound_springs.audio import AudioBuffer, AudioDecodeError, load_audio_file
from sound_springs.pipeline import AnalysisSettings, run_pipeline
from sound_springs.render import create_diagnostic_figure


def select_analysis_channel(audio: AudioBuffer, requested_channel: int | None) -> int:
    """Resolve a channel without silently defining a stereo mixdown policy."""
    if requested_channel is None:
        if audio.channel_count == 1:
            return 0
        raise ValueError(
            f"input has {audio.channel_count} channels; choose one explicitly "
            "with --channel (zero-based)"
        )
    if not 0 <= requested_channel < audio.channel_count:
        raise ValueError(
            f"channel {requested_channel} is out of range for "
            f"{audio.channel_count} channel(s)"
        )
    return requested_channel


def build_argument_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description=(
            "Decode a WAV or FLAC file, measure one frequency over time, "
            "drive a damped spring, and render diagnostic plots."
        )
    )
    parser.add_argument("audio_file", type=Path, help="WAV or FLAC file to analyze")
    parser.add_argument(
        "--channel",
        type=int,
        help="zero-based channel to analyze (required for multichannel input)",
    )
    parser.add_argument(
        "--frequency",
        type=float,
        default=440.0,
        help="target frequency to measure in Hz (default: 440)",
    )
    parser.add_argument("--frame-length", type=int, default=2_048)
    parser.add_argument("--hop-length", type=int, default=512)
    parser.add_argument("--save", type=Path, help="save the diagnostic figure")
    parser.add_argument(
        "--no-show",
        action="store_true",
        help="calculate without opening an interactive window",
    )
    return parser


def main(arguments: Sequence[str] | None = None) -> None:
    parser = build_argument_parser()
    options = parser.parse_args(arguments)

    try:
        audio = load_audio_file(options.audio_file)
        channel_index = select_analysis_channel(audio, options.channel)
        settings = AnalysisSettings(
            frame_length=options.frame_length,
            hop_length=options.hop_length,
            target_frequency_hz=options.frequency,
        )
        signal = audio.channel(channel_index)
        result = run_pipeline(signal, audio.sample_rate, settings)
    except (AudioDecodeError, FileNotFoundError, ValueError) as error:
        parser.error(str(error))

    strongest_bin_index = int(result.representative_amplitudes.argmax())
    print(f"Source: {options.audio_file}")
    print(f"Sample rate: {audio.sample_rate} Hz")
    print(f"Decoded frames: {audio.frame_count}")
    print(f"Channels: {audio.channel_count}; analyzed channel: {channel_index}")
    print(f"Analysis frames: {len(result.target_amplitudes)}")
    print(
        f"FFT bin nearest {settings.target_frequency_hz:g} Hz: "
        f"{result.target_bin_index} ({result.measured_frequency_hz:.2f} Hz)"
    )
    print(
        "Strongest frequency in representative frame: "
        f"{result.frequencies[strongest_bin_index]:.2f} Hz"
    )

    figure = create_diagnostic_figure(
        signal,
        result,
        source_label=options.audio_file.name,
    )
    if options.save is not None:
        figure.savefig(options.save)
        print(f"Saved diagnostic figure: {options.save}")
    if not options.no_show:
        plt.show()
    plt.close(figure)


if __name__ == "__main__":
    main()
