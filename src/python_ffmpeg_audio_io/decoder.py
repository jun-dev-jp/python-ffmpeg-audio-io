"""Audio decoder module using FFmpeg and FFprobe."""

from __future__ import annotations

import subprocess
from os import R_OK, PathLike, access
from pathlib import Path

from ._validation import (
    validate_channels_opt,
    validate_duration,
    validate_sample_rate_opt,
    validate_start_time,
)
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
    sample_rate: PCMSampleRate | None = None,
    channels: PCMChannels | None = None,
    start_time: float | int | None = None,
    duration: float | int | None = None,
) -> PCM:
    """Decode an audio file to uncompressed raw PCM data using FFmpeg.

    Args:
        path: Path to the input audio file.
        pcm_codec: The PCM codec to use for decoding (default: PCM_F32LE).
        sample_rate: Target sample rate for resampling, or None to keep original
            (default: None).
        channels: Target channels for channel conversion, or None to keep original
            (default: None).
        start_time: Starting offset in seconds to seek before decoding, or None
            (default: None).
        duration: Duration in seconds of audio to decode, or None to decode to end
            (default: None).

    Returns:
        PCM: A dataclass instance containing the decoded PCM raw bytes and metadata.

    Raises:
        AudioTypeError: If arguments are of incorrect type.
        AudioValueError: If metadata parsing fails, arguments have invalid values,
            or audio channels/sample rate are not supported by PCMChannels /
            PCMSampleRate.
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

    target_sample_rate = validate_sample_rate_opt(sample_rate)
    target_channels = validate_channels_opt(channels)
    seek_time = validate_start_time(start_time)
    cut_duration = validate_duration(duration)

    audio_path = Path(path)
    if not audio_path.exists():
        raise FileReadError(f"Audio file not found: {audio_path}")
    if not audio_path.is_file():
        raise FileReadError(f"Audio file is not a regular file: {audio_path}")
    if not access(audio_path, R_OK):
        raise FileReadError(f"Audio file is not readable: {audio_path}")

    if target_channels is None or target_sample_rate is None:
        audio_info = get_audio_info(audio_path)
        if target_channels is None:
            try:
                target_channels = PCMChannels(audio_info.channels)
            except ValueError as e:
                msg = (
                    f"Unsupported channel count '{audio_info.channels}' "
                    f"in audio file: {audio_path}"
                )
                raise AudioValueError(msg) from e

        if target_sample_rate is None:
            try:
                target_sample_rate = PCMSampleRate(audio_info.sample_rate)
            except ValueError as e:
                msg = (
                    f"Unsupported sample rate '{audio_info.sample_rate}' "
                    f"in audio file: {audio_path}"
                )
                raise AudioValueError(msg) from e

    sample_format = pcm_codec.pcm_format

    cmd = ["ffmpeg"]
    if seek_time is not None:
        cmd.extend(["-ss", str(seek_time)])
    cmd.extend(
        [
            "-i",
            str(audio_path),
            "-v",
            "error",
        ]
    )
    if cut_duration is not None:
        cmd.extend(["-t", str(cut_duration)])
    cmd.extend(
        [
            "-f",
            sample_format.value,
            "-acodec",
            pcm_codec.value,
            "-ar",
            str(target_sample_rate.value),
            "-ac",
            str(target_channels.value),
            "pipe:1",
        ]
    )

    try:
        result = subprocess.run(cmd, capture_output=True, check=True)
        return PCM(
            data=result.stdout,
            format=sample_format,
            sample_rate=target_sample_rate,
            channels=target_channels,
        )
    except FileNotFoundError as e:
        raise FFmpegNotFoundError(
            "ffmpeg executable not found. Please ensure FFmpeg is in PATH."
        ) from e
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
