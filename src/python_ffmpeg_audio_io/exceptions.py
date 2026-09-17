"""Exceptions for python-ffmpeg-audio-io."""

from __future__ import annotations


class PyFFmpegAudioIOError(Exception):
    """Base exception for all python-ffmpeg-audio-io errors."""

    stderr: str

    def __init__(self, message: str, stderr: str = "") -> None:
        super().__init__(message)
        self.stderr = stderr


class AudioTypeError(PyFFmpegAudioIOError, TypeError):
    """Raised when an argument has an invalid type."""


class AudioValueError(PyFFmpegAudioIOError, ValueError):
    """Raised when an argument has an invalid value."""


class AudioIOError(PyFFmpegAudioIOError, OSError):
    """Base exception for audio file I/O operations."""


class FileReadError(AudioIOError):
    """Raised when a file cannot be read or does not exist."""


class FileWriteError(AudioIOError):
    """Raised when a file cannot be written or output destination is invalid."""


class FFmpegError(PyFFmpegAudioIOError):
    """Raised when an ffmpeg or ffprobe subprocess fails or returns an error."""


class FFmpegNotFoundError(FFmpegError, FileNotFoundError):
    """Raised when ffmpeg or ffprobe executable is not found on the system."""


class PCMFormatError(AudioValueError):
    """Raised when the PCM format is not supported or misaligned."""


class StreamError(PyFFmpegAudioIOError):
    """Base exception for audio stream errors."""


AudioStreamError = StreamError


class StreamClosedError(StreamError):
    """Raised when an I/O operation is attempted on a closed audio stream."""


class StreamBrokenError(StreamError, BrokenPipeError):
    """Raised when an audio stream pipe is broken or process terminates unexpectedly."""


__all__ = [
    "AudioIOError",
    "AudioStreamError",
    "AudioTypeError",
    "AudioValueError",
    "FFmpegError",
    "FFmpegNotFoundError",
    "FileReadError",
    "FileWriteError",
    "PCMFormatError",
    "PyFFmpegAudioIOError",
    "StreamBrokenError",
    "StreamClosedError",
    "StreamError",
]
