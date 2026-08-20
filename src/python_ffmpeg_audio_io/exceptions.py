"""Exceptions for python-ffmpeg-audio-io."""

from __future__ import annotations


class PyFFmpegAudioIOError(Exception):
    """Base exception for all python-ffmpeg-audio-io errors."""

    stderr: str

    def __init__(self, message: str, stderr: str = "") -> None:
        super().__init__(message)
        self.stderr = stderr


class FileReadError(PyFFmpegAudioIOError):
    """Raised when a file cannot be read or does not exist."""


class FileWriteError(PyFFmpegAudioIOError):
    """Raised when a file cannot be written or output destination is invalid."""


class FFmpegError(PyFFmpegAudioIOError):
    """Raised when an ffmpeg or ffprobe subprocess fails or returns an error."""


class FFmpegNotFoundError(PyFFmpegAudioIOError):
    """Raised when ffmpeg or ffprobe executable is not found on the system."""


class PCMFormatError(PyFFmpegAudioIOError):
    """Raised when the PCM format is not supported."""
