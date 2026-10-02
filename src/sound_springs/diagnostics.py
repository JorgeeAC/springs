"""Small, centralized records for one-off runtime diagnostics."""

from __future__ import annotations

import csv
import re
import sys
from contextlib import contextmanager
from dataclasses import dataclass, field
from datetime import UTC, datetime
from pathlib import Path
from time import perf_counter
from types import MappingProxyType
from typing import Iterator, Mapping


MetricValue = str | int | float | None


CSV_COLUMNS = (
    "run_id",
    "timestamp_utc",
    "file_name",
    "audio_duration_s",
    "file_size_bytes",
    "file_size_mib",
    "sample_rate_hz",
    "channel_count",
    "analyzed_channel_index",
    "decoded_frame_count",
    "decoded_sample_count",
    "decoded_dtype",
    "decoded_array_bytes",
    "decoded_array_mib",
    "decode_s",
    "analysis_s",
    "dsp_analysis_s",
    "timeline_s",
    "mapping_simulation_s",
    "total_prepare_s",
    "analysis_realtime_factor",
    "frame_size_samples",
    "hop_size_samples",
    "fft_size_samples",
    "fft_bin_count",
    "target_frequency_hz",
    "analysis_frame_count",
    "timeline_array_bytes",
    "timeline_array_mib",
    "precomputed_state_bytes",
    "precomputed_state_mib",
    "memory_before_load_rss_mib",
    "memory_after_decode_rss_mib",
    "memory_after_analysis_rss_mib",
    "memory_end_rss_mib",
    "peak_rss_mib",
    "decode_rss_delta_mib",
    "analysis_rss_delta_mib",
    "total_prepare_rss_delta_mib",
    "release_rss_delta_mib",
    "current_rss_source",
    "peak_rss_source",
    "python_version",
    "platform",
)


_RUN_ID_PATTERN = re.compile(r"^[A-Za-z0-9][A-Za-z0-9_.-]*$")


def _utc_now() -> datetime:
    return datetime.now(UTC)


def _default_run_id() -> str:
    return _utc_now().strftime("%Y%m%dT%H%M%S.%fZ")


def _default_timestamp() -> str:
    return _utc_now().isoformat(timespec="seconds")


@dataclass
class DiagnosticRun:
    """Collect scalar measurements and write one coherent run record.

    Producers only call record or measure. CSV and text output are kept here
    so pipeline and DSP code never know about file formats.
    """

    run_id: str = field(default_factory=_default_run_id)
    timestamp_utc: str = field(default_factory=_default_timestamp)
    _metrics: dict[str, MetricValue] = field(default_factory=dict, init=False)

    def __post_init__(self) -> None:
        if not _RUN_ID_PATTERN.fullmatch(self.run_id):
            raise ValueError(
                "run_id must start with an alphanumeric character and contain "
                "only letters, numbers, dots, underscores, or hyphens"
            )

    @property
    def metrics(self) -> Mapping[str, MetricValue]:
        """Expose collected values without allowing external mutation."""
        return MappingProxyType(self._metrics)

    def record(self, name: str, value: MetricValue) -> None:
        """Add one measurement, rejecting misspelled or duplicate fields."""
        if name not in CSV_COLUMNS or name in {"run_id", "timestamp_utc"}:
            raise ValueError(f"unknown or reserved diagnostic metric: {name}")
        if name in self._metrics:
            raise ValueError(f"diagnostic metric already recorded: {name}")
        if value is not None and not isinstance(value, (str, int, float)):
            raise TypeError("diagnostic metrics must be scalar strings or numbers")
        self._metrics[name] = value

    @contextmanager
    def measure(self, name: str) -> Iterator[None]:
        """Record elapsed wall-clock seconds for one named phase."""
        started = perf_counter()
        try:
            yield
        finally:
            self.record(name, perf_counter() - started)

    def row(self) -> dict[str, MetricValue]:
        """Return a complete stable-schema row; absent optional values are null."""
        values: dict[str, MetricValue] = {
            "run_id": self.run_id,
            "timestamp_utc": self.timestamp_utc,
        }
        values.update(self._metrics)
        return {column: values.get(column) for column in CSV_COLUMNS}

    def write_outputs(self, output_directory: str | Path) -> tuple[Path, Path]:
        """Write exactly one CSV row and one compact text summary."""
        output_path = Path(output_directory)
        output_path.mkdir(parents=True, exist_ok=True)
        csv_path = output_path / f"{self.run_id}.csv"
        text_path = output_path / f"{self.run_id}.txt"

        with csv_path.open("w", encoding="utf-8", newline="") as csv_file:
            writer = csv.DictWriter(csv_file, fieldnames=CSV_COLUMNS)
            writer.writeheader()
            writer.writerow(self.row())

        text_path.write_text(self.text_summary(), encoding="utf-8")
        return csv_path, text_path

    def text_summary(self) -> str:
        """Render the human companion to the canonical CSV record."""
        row = self.row()

        def number(name: str, decimals: int = 3) -> str:
            value = row[name]
            if value is None:
                return "not available"
            return f"{float(value):.{decimals}f}"

        duration = number("audio_duration_s")
        realtime = number("analysis_realtime_factor", 1)
        analysis_delta = number("analysis_rss_delta_mib")
        peak = number("peak_rss_mib")
        interpretation = (
            f"Analysis completed at {realtime}x realtime. Current RSS changed by "
            f"{analysis_delta} MiB from the post-decode snapshot to the "
            "post-analysis snapshot. This single process run is not an "
            "album-wide or cross-platform performance bound."
        )

        return (
            "Sound Springs diagnostic run\n"
            "----------------------------\n\n"
            f"Run: {self.run_id}\n"
            f"Track: {row['file_name'] or 'not available'}\n"
            f"Duration: {duration} s\n"
            f"Input size: {number('file_size_mib')} MiB\n"
            f"Decoded PCM: {number('decoded_array_mib')} MiB\n\n"
            "Decode:\n"
            f"  Time: {number('decode_s')} s\n"
            f"  RSS delta: {number('decode_rss_delta_mib')} MiB\n\n"
            "Analysis:\n"
            f"  Time: {number('analysis_s')} s\n"
            f"  DSP time: {number('dsp_analysis_s')} s\n"
            f"  Timeline time: {number('timeline_s')} s\n"
            f"  Speed: {realtime}x realtime\n"
            f"  Frames: {row['analysis_frame_count'] or 'not available'}\n"
            f"  Stored precomputed state: "
            f"{number('precomputed_state_mib')} MiB\n"
            f"  RSS delta: {analysis_delta} MiB\n\n"
            "Overall:\n"
            f"  Preparation time: {number('total_prepare_s')} s\n"
            f"  Live-state RSS delta: "
            f"{number('total_prepare_rss_delta_mib')} MiB\n"
            f"  Peak process RSS: {peak} MiB\n"
            f"  End RSS after release: {number('memory_end_rss_mib')} MiB\n\n"
            "Interpretation:\n"
            f"  {interpretation}\n\n"
            "Memory note:\n"
            "  RSS is process-level resident memory, not Python object size. "
            "Peak RSS is the process lifetime high-water mark. Allocator and "
            "OS behavior can keep freed memory resident.\n"
        )


@dataclass(frozen=True)
class ProcessMemorySnapshot:
    """One lightweight process-resident-memory observation."""

    current_rss_mib: float | None
    peak_rss_mib: float | None
    current_source: str | None
    peak_source: str | None


def process_memory_snapshot() -> ProcessMemorySnapshot:
    """Read Linux process RSS and lifetime peak RSS from /proc when present."""
    current_rss_mib: float | None = None
    peak_rss_mib: float | None = None
    current_source: str | None = None
    peak_source: str | None = None

    status_path = Path("/proc/self/status")
    if status_path.is_file():
        status_values: dict[str, int] = {}
        for line in status_path.read_text(encoding="utf-8").splitlines():
            name, separator, remainder = line.partition(":")
            if separator and name in {"VmRSS", "VmHWM"}:
                fields = remainder.split()
                if len(fields) >= 2 and fields[1] == "kB":
                    status_values[name] = int(fields[0])
        if "VmRSS" in status_values:
            current_rss_mib = status_values["VmRSS"] / 1024
            current_source = "linux_proc_status_vmrss"
        if "VmHWM" in status_values:
            peak_rss_mib = status_values["VmHWM"] / 1024
            peak_source = "linux_proc_status_vmhwm_process_lifetime"

    return ProcessMemorySnapshot(
        current_rss_mib=current_rss_mib,
        peak_rss_mib=peak_rss_mib,
        current_source=current_source,
        peak_source=peak_source,
    )


def runtime_identity() -> tuple[str, str]:
    """Return concise Python and platform labels for benchmark context."""
    return sys.version.split()[0], sys.platform
