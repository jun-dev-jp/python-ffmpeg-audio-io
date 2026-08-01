"""Audio metadata parsing and ffprobe wrapper module."""

from __future__ import annotations

import json
import subprocess
from dataclasses import dataclass
from enum import Enum
from pathlib import Path
from typing import Any

from .exceptions import FFmpegError, FFmpegNotFoundError, PyFFmpegAudioIOError

PathLike = str | Path


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


class FFprobeLogLevel(Enum):
    """FFprobe log level."""

    QUIET = "quiet"
    PANIC = "panic"
    FATAL = "fatal"
    ERROR = "error"  # recommended
    WARNING = "warning"
    INFO = "info"  # default
    VERBOSE = "verbose"
    DEBUG = "debug"
    TRACE = "trace"


def get_audio_info_from_ffprobe(file_path: PathLike) -> AudioInfo:
    """Parse audio information from FFprobe output.

    Args:
        file_path: Path to the audio file.

    Returns:
        AudioInfo containing parsed metadata.

    Raises:
        FileNotFoundError: If the audio file does not exist.
        FFmpegError: If ffprobe fails to run or output is invalid.
        PyFFmpegAudioIOError: If no audio stream is found or attributes are invalid.
    """
    data = run_ffprobe(file_path=file_path)

    streams = data.get("streams", [])
    if not streams:
        raise PyFFmpegAudioIOError("No streams found in FFprobe output")

    try:
        stream = next(s for s in streams if s.get("codec_type") == "audio")
    except StopIteration:
        raise PyFFmpegAudioIOError("No audio stream found in FFprobe output") from None

    format_data = data.get("format", {})

    try:
        return AudioInfo(
            sample_rate=int(stream["sample_rate"]),
            sample_fmt=str(stream.get("sample_fmt", "")),
            channels=int(stream["channels"]),
            duration=float(stream["duration"]),
            codec_name=str(stream.get("codec_name", "")),
            format_name=str(format_data.get("format_name", "")),
            format_long_name=str(format_data.get("format_long_name", "")),
            size=int(format_data.get("size", 0)),
            bit_rate=int(format_data.get("bit_rate", 0)),
        )
    except (KeyError, TypeError, ValueError) as e:
        raise PyFFmpegAudioIOError(f"Failed to parse AudioInfo attributes: {e}") from e


def run_ffprobe(
    file_path: PathLike, log_level: FFprobeLogLevel = FFprobeLogLevel.ERROR
) -> dict[str, Any]:
    """Run FFprobe and return the output as a dictionary.

    Args:
        file_path: Path to the audio file.
        log_level: FFprobe log level (default: ERROR).

    Returns:
        Dictionary containing the FFprobe output.

    Raises:
        FileNotFoundError: If the audio file does not exist.
        FFmpegError: If ffprobe fails to inspect the file or output is invalid JSON.
    """
    path = Path(file_path)
    if not path.exists():
        raise FileNotFoundError(f"Audio file not found: {path}")

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
        result = subprocess.run(cmd, capture_output=True, text=True, check=True)
    except subprocess.CalledProcessError as e:
        stderr_msg = e.stderr.strip() if e.stderr else ""
        raise FFmpegError(
            f"ffprobe failed to inspect {path}: {stderr_msg}",
            stderr=e.stderr,
        ) from e
    except OSError as e:
        if e.errno == 2:
            raise FFmpegNotFoundError(
                "ffprobe executable not found. Please ensure FFmpeg is installed and available in your PATH."
            ) from e
        raise FFmpegError(f"Failed to start ffprobe process: {e}") from e

    try:
        return json.loads(result.stdout)
    except json.JSONDecodeError as e:
        raise FFmpegError(f"Invalid FFprobe JSON output: {e}") from e
