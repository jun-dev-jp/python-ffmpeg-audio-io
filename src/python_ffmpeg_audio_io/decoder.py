"""Audio decoder module using ffmpeg and ffprobe."""

from __future__ import annotations

import subprocess
from pathlib import Path

from .exceptions import FFmpegError, FFmpegNotFoundError
from .ffprobe import get_audio_info_from_ffprobe
from .pcm import PCMChannels, PCMCodec, PCMFormat, PCMSampleRate

PathLike = str | Path


def decode_to_PCM_F32LE_with_ffmpeg(
    path: PathLike,
) -> tuple[bytes, PCMSampleRate, PCMChannels]:
    """Decode audio data from a file path to PCM F32LE using ffmpeg.

    Args:
        path: Path to the audio file.

    Returns:
        tuple[bytes, PCMSampleRate, PCMChannels]: The decoded PCM data, sample rate, and channels.

    Raises:
        FileNotFoundError: If the audio file does not exist.
        FFmpegError: If ffprobe or ffmpeg fails to run or output is invalid.
        PyFFmpegAudioIOError: If no audio stream is found or attributes are invalid.
    """
    audio_path = Path(path)
    if not audio_path.exists():
        raise FileNotFoundError(f"Audio file not found: {audio_path}")

    audio_info = get_audio_info_from_ffprobe(audio_path)
    pcm_channels = PCMChannels(audio_info.channels)
    pcm_sample_rate = PCMSampleRate(audio_info.sample_rate)

    pcm_codec = PCMCodec.PCM_F32LE
    # Extract PCM format from codec enum value (e.g., "pcm_f32le" -> "f32le")
    sample_format = PCMFormat(pcm_codec.value.split("_")[1].lower())

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
        process = subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        stdout, stderr = process.communicate()
        if process.returncode != 0:
            err_msg = stderr.decode("utf-8", errors="ignore").strip()
            raise FFmpegError(
                f"ffmpeg failed to decode {audio_path}: {err_msg}",
                stderr=err_msg,
            )
        return stdout, pcm_sample_rate, pcm_channels
    except OSError as e:
        if e.errno == 2:  # No such file or directory
            raise FFmpegNotFoundError(
                "ffmpeg executable not found. Please ensure FFmpeg is installed and available in your PATH."
            ) from e
        raise FFmpegError(f"Failed to start ffmpeg process: {e}") from e
    except subprocess.CalledProcessError as e:
        err_msg = (
            e.stderr.decode("utf-8", errors="ignore").strip()
            if isinstance(e.stderr, bytes)
            else str(e.stderr)
        )
        raise FFmpegError(
            f"ffmpeg failed to decode {audio_path}: {err_msg}",
            stderr=err_msg,
        ) from e
