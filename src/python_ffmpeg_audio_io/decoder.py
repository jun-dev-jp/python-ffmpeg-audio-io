"""Audio decoder module using FFmpeg and FFprobe."""

from __future__ import annotations

import subprocess
from os import R_OK, PathLike, access
from pathlib import Path

from .exceptions import (
    AudioTypeError,
    AudioValueError,
    FFmpegError,
    FFmpegNotFoundError,
    FileReadError,
)
from .ffprobe import get_audio_info
from .pcm import PCM, PCMChannels, PCMCodec, PCMSampleRate


def decode(
    path: str | PathLike[str],
    pcm_codec: PCMCodec = PCMCodec.PCM_F32LE,
) -> PCM:
    """Decode an audio file to uncompressed raw PCM data using FFmpeg.

    Args:
        path: Path to the input audio file.
        pcm_codec: The PCM codec to use for decoding (default: PCM_F32LE).

    Returns:
        PCM: A dataclass instance containing the decoded PCM raw bytes and metadata.

    Raises:
        AudioTypeError: If arguments are of incorrect type.
        AudioValueError: If metadata parsing fails or audio channels/sample rate
            are not supported by PCMChannels / PCMSampleRate.
        FileReadError: If the audio file does not exist or is unreadable.
        FFmpegNotFoundError: If FFmpeg or FFprobe executable is not found in PATH.
        FFmpegError: If decoding fails or FFmpeg returns an error.
        PyFFmpegAudioIOError: Base class for all above errors.
    """
    if not isinstance(path, (str, PathLike)):
        raise AudioTypeError(
            f"path must be a str or PathLike, got {type(path).__name__}"
        )
    if not isinstance(pcm_codec, PCMCodec):
        t_name = type(pcm_codec).__name__
        raise AudioTypeError(f"pcm_codec must be an instance of PCMCodec, got {t_name}")

    audio_path = Path(path)
    if not audio_path.exists():
        raise FileReadError(f"Audio file not found: {audio_path}")
    if not audio_path.is_file():
        raise FileReadError(f"Audio file is not a regular file: {audio_path}")
    if not access(audio_path, R_OK):
        raise FileReadError(f"Audio file is not readable: {audio_path}")

    audio_info = get_audio_info(audio_path)

    try:
        pcm_channels = PCMChannels(audio_info.channels)
    except ValueError as e:
        msg = (
            f"Unsupported channel count '{audio_info.channels}' "
            f"in audio file: {audio_path}"
        )
        raise AudioValueError(msg) from e

    try:
        pcm_sample_rate = PCMSampleRate(audio_info.sample_rate)
    except ValueError as e:
        msg = (
            f"Unsupported sample rate '{audio_info.sample_rate}' "
            f"in audio file: {audio_path}"
        )
        raise AudioValueError(msg) from e

    sample_format = pcm_codec.pcm_format

    cmd = [
        "ffmpeg",
        "-i",
        str(audio_path),
        "-v",
        "error",
        "-f",
        sample_format.value,
        "-acodec",
        pcm_codec.value,
        "-ar",
        str(pcm_sample_rate.value),
        "-ac",
        str(pcm_channels.value),
        "pipe:1",
    ]

    try:
        result = subprocess.run(cmd, capture_output=True, check=True)
        return PCM(
            data=result.stdout,
            format=sample_format,
            sample_rate=pcm_sample_rate,
            channels=pcm_channels,
        )
    except OSError as e:
        if e.errno == 2:
            raise FFmpegNotFoundError(
                "ffmpeg executable not found. Please ensure FFmpeg is in PATH."
            ) from e
        raise FFmpegError(f"Failed to start ffmpeg process: {e}") from e
    except subprocess.CalledProcessError as e:
        err_msg = (
            e.stderr.decode("utf-8", errors="ignore").strip()
            if isinstance(e.stderr, (bytes, bytearray))
            else str(e.stderr or "")
        )
        raise FFmpegError(
            f"ffmpeg failed to decode {audio_path}: {err_msg}",
            stderr=err_msg,
        ) from e


__all__ = ["decode"]
