"""Exceptions for python-ffmpeg-audio-io."""


class PyFFmpegAudioIOError(Exception):
    """Base exception for all python-ffmpeg-audio-io errors."""

    def __init__(self, message: str, stderr: str = "") -> None:
        super().__init__(message)
        self.stderr = stderr


class FFmpegError(PyFFmpegAudioIOError):
    """Raised when an ffmpeg or ffprobe subprocess fails or returns an error."""


class FFmpegNotFoundError(PyFFmpegAudioIOError):
    """Raised when ffmpeg or ffprobe executable is not found on the system."""
