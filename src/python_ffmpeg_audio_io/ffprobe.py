"""Audio metadata parsing and ffprobe wrapper module."""

from __future__ import annotations

import json
import subprocess
from dataclasses import dataclass
from enum import Enum
from os import R_OK, PathLike, access
from pathlib import Path

from .exceptions import (
    AudioTypeError,
    AudioValueError,
    FFmpegError,
    FFmpegNotFoundError,
    FileReadError,
    PyFFmpegAudioIOError,
)


@dataclass(frozen=True)
class AudioInfo:
    """Audio information parsed from FFprobe output."""

    sample_rate: int
    sample_fmt: str
    channels: int
    duration: float
    codec_name: str
    format_name: str
    format_long_name: str
    size: int
    bit_rate: int

    def __post_init__(self) -> None:
        """Validate fields upon initialization."""
        if not isinstance(self.sample_rate, int) or self.sample_rate <= 0:
            raise AudioValueError(
                f"sample_rate must be a positive integer, got {self.sample_rate}"
            )
        if not isinstance(self.channels, int) or self.channels <= 0:
            raise AudioValueError(
                f"channels must be a positive integer, got {self.channels}"
            )
        if not isinstance(self.duration, (int, float)) or self.duration < 0:
            raise AudioValueError(
                f"duration must be a non-negative float, got {self.duration}"
            )
        if not isinstance(self.sample_fmt, str):
            raise AudioTypeError(
                f"sample_fmt must be a str, got {type(self.sample_fmt).__name__}"
            )
        if not isinstance(self.codec_name, str):
            raise AudioTypeError(
                f"codec_name must be a str, got {type(self.codec_name).__name__}"
            )
        if not isinstance(self.format_name, str):
            raise AudioTypeError(
                f"format_name must be a str, got {type(self.format_name).__name__}"
            )
        if not isinstance(self.format_long_name, str):
            t_name = type(self.format_long_name).__name__
            raise AudioTypeError(f"format_long_name must be a str, got {t_name}")
        if not isinstance(self.size, int) or self.size < 0:
            raise AudioValueError(
                f"size must be a non-negative integer, got {self.size}"
            )
        if not isinstance(self.bit_rate, int) or self.bit_rate < 0:
            raise AudioValueError(
                f"bit_rate must be a non-negative integer, got {self.bit_rate}"
            )


class FFprobeLogLevel(Enum):
    """FFprobe log level options."""

    QUIET = "quiet"
    PANIC = "panic"
    FATAL = "fatal"
    ERROR = "error"
    WARNING = "warning"
    INFO = "info"
    VERBOSE = "verbose"
    DEBUG = "debug"
    TRACE = "trace"


def get_audio_info(file_path: str | PathLike[str]) -> AudioInfo:
    """Parse audio information from FFprobe output.

    Args:
        file_path: Path to the audio file.

    Returns:
        AudioInfo containing parsed metadata.

    Raises:
        AudioTypeError: If file_path is not a str or PathLike.
        FileReadError: If the audio file does not exist or is unreadable.
        FFmpegNotFoundError: If ffprobe is not installed or not found in PATH.
        FFmpegError: If ffprobe fails to run or output is invalid.
        PyFFmpegAudioIOError: If no audio stream is found or parsing fails.
    """
    if not isinstance(file_path, (str, PathLike)):
        raise AudioTypeError(
            f"file_path must be a str or PathLike, got {type(file_path).__name__}"
        )

    data = run_ffprobe(file_path=file_path)

    raw_streams = data.get("streams")
    streams: list[dict[str, object]] = (
        raw_streams if isinstance(raw_streams, list) else []
    )
    if not streams:
        raise PyFFmpegAudioIOError("No streams found in FFprobe output")

    audio_stream: dict[str, object] | None = None
    for s in streams:
        if isinstance(s, dict) and s.get("codec_type") == "audio":
            audio_stream = s
            break

    if audio_stream is None:
        raise PyFFmpegAudioIOError("No audio stream found in FFprobe output")

    raw_format = data.get("format")
    format_data: dict[str, object] = raw_format if isinstance(raw_format, dict) else {}

    try:
        sample_rate_val = audio_stream.get("sample_rate")
        sample_rate = int(str(sample_rate_val))

        sample_fmt = str(audio_stream.get("sample_fmt") or "")

        channels_val = audio_stream.get("channels")
        channels = int(str(channels_val))

        duration_val = (
            audio_stream.get("duration") or format_data.get("duration") or 0.0
        )
        duration = float(str(duration_val))

        codec_name = str(audio_stream.get("codec_name") or "")
        format_name = str(format_data.get("format_name") or "")
        format_long_name = str(format_data.get("format_long_name") or "")

        size_val = format_data.get("size")
        size = (
            int(str(size_val))
            if size_val is not None
            else Path(file_path).stat().st_size
        )

        bit_rate_val = format_data.get("bit_rate") or audio_stream.get("bit_rate") or 0
        bit_rate = int(str(bit_rate_val))

        return AudioInfo(
            sample_rate=sample_rate,
            sample_fmt=sample_fmt,
            channels=channels,
            duration=duration,
            codec_name=codec_name,
            format_name=format_name,
            format_long_name=format_long_name,
            size=size,
            bit_rate=bit_rate,
        )
    except (KeyError, TypeError, ValueError) as e:
        raise PyFFmpegAudioIOError(f"Failed to parse AudioInfo attributes: {e}") from e


def run_ffprobe(
    file_path: str | PathLike[str],
    log_level: FFprobeLogLevel = FFprobeLogLevel.ERROR,
) -> dict[str, object]:
    """Run FFprobe and return the parsed JSON output.

    Args:
        file_path: Path to the audio file.
        log_level: FFprobe log level (default: ERROR).

    Returns:
        Dictionary containing the parsed FFprobe JSON output.

    Raises:
        AudioTypeError: If arguments are of incorrect type.
        FileReadError: If the audio file does not exist or is unreadable.
        FFmpegNotFoundError: If ffprobe is not installed or not found in PATH.
        FFmpegError: If ffprobe fails to inspect the file or output is invalid JSON.
    """
    if not isinstance(file_path, (str, PathLike)):
        raise AudioTypeError(
            f"file_path must be a str or PathLike, got {type(file_path).__name__}"
        )
    if not isinstance(log_level, FFprobeLogLevel):
        t_name = type(log_level).__name__
        msg = f"log_level must be an instance of FFprobeLogLevel, got {t_name}"
        raise AudioTypeError(msg)

    path = Path(file_path)
    if not path.exists():
        raise FileReadError(f"Audio file not found: {path}")
    if not path.is_file():
        raise FileReadError(f"Audio file is not a regular file: {path}")
    if not access(path, R_OK):
        raise FileReadError(f"Audio file is not readable: {path}")

    cmd = [
        "ffprobe",
        "-v",
        log_level.value,
        "-print_format",
        "json",
        "-show_format",
        "-show_streams",
        str(path),
    ]

    try:
        result = subprocess.run(
            cmd,
            capture_output=True,
            check=True,
            stdin=subprocess.DEVNULL,
        )
    except FileNotFoundError as e:
        raise FFmpegNotFoundError(
            "ffprobe executable not found. Please ensure FFmpeg is in PATH."
        ) from e
    except OSError as e:
        raise FFmpegError(f"Failed to start ffprobe process: {e}") from e
    except subprocess.CalledProcessError as e:
        stderr_str = (
            e.stderr.decode("utf-8", errors="replace").strip()
            if isinstance(e.stderr, bytes)
            else str(e.stderr or "").strip()
        )
        raise FFmpegError(
            f"ffprobe failed to inspect {path}: {stderr_str}",
            stderr=stderr_str,
        ) from e

    try:
        stdout_str = (
            result.stdout.decode("utf-8", errors="replace")
            if isinstance(result.stdout, bytes)
            else str(result.stdout or "")
        )
        parsed_data = json.loads(stdout_str)
        if not isinstance(parsed_data, dict):
            raise FFmpegError(f"Unexpected JSON structure from FFprobe for {path}")
        return parsed_data  # type: ignore[return-value]
    except json.JSONDecodeError as e:
        raise FFmpegError(f"Invalid FFprobe JSON output for {path}: {e}") from e


__all__ = [
    "AudioInfo",
    "FFprobeLogLevel",
    "get_audio_info",
    "run_ffprobe",
]
