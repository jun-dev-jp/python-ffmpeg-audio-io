"""Tests for custom exception hierarchy."""

from __future__ import annotations

import pytest

from python_ffmpeg_audio_io import (
    AudioIOError,
    AudioStreamError,
    AudioTypeError,
    AudioValueError,
    FFmpegError,
    FFmpegNotFoundError,
    FileReadError,
    FileWriteError,
    PCMFormatError,
    PyFFmpegAudioIOError,
    StreamBrokenError,
    StreamClosedError,
    StreamError,
    decode,
    get_audio_info,
)


def test_exception_inheritance_hierarchy() -> None:
    """Verify that all exceptions inherit from PyFFmpegAudioIOError."""
    # Base
    assert issubclass(PyFFmpegAudioIOError, Exception)

    # Type & Value errors
    assert issubclass(AudioTypeError, PyFFmpegAudioIOError)
    assert issubclass(AudioTypeError, TypeError)

    assert issubclass(AudioValueError, PyFFmpegAudioIOError)
    assert issubclass(AudioValueError, ValueError)

    assert issubclass(PCMFormatError, AudioValueError)
    assert issubclass(PCMFormatError, PyFFmpegAudioIOError)
    assert issubclass(PCMFormatError, ValueError)

    # File & IO errors
    assert issubclass(AudioIOError, PyFFmpegAudioIOError)
    assert issubclass(AudioIOError, OSError)

    assert issubclass(FileReadError, AudioIOError)
    assert issubclass(FileReadError, PyFFmpegAudioIOError)

    assert issubclass(FileWriteError, AudioIOError)
    assert issubclass(FileWriteError, PyFFmpegAudioIOError)

    # FFmpeg subprocess errors
    assert issubclass(FFmpegError, PyFFmpegAudioIOError)

    assert issubclass(FFmpegNotFoundError, FFmpegError)
    assert issubclass(FFmpegNotFoundError, FileNotFoundError)
    assert issubclass(FFmpegNotFoundError, PyFFmpegAudioIOError)

    # Stream errors
    assert issubclass(StreamError, PyFFmpegAudioIOError)
    assert AudioStreamError is StreamError

    assert issubclass(StreamClosedError, StreamError)
    assert issubclass(StreamClosedError, PyFFmpegAudioIOError)

    assert issubclass(StreamBrokenError, StreamError)
    assert issubclass(StreamBrokenError, BrokenPipeError)
    assert issubclass(StreamBrokenError, PyFFmpegAudioIOError)


def test_catch_all_via_base_exception() -> None:
    """Verify that catching PyFFmpegAudioIOError catches all custom exceptions."""
    exceptions_to_test = [
        AudioTypeError("type error"),
        AudioValueError("value error"),
        PCMFormatError("pcm format error"),
        AudioIOError("io error"),
        FileReadError("file read error"),
        FileWriteError("file write error"),
        FFmpegError("ffmpeg error", stderr="some stderr"),
        FFmpegNotFoundError("not found"),
        StreamError("stream error"),
        StreamClosedError("stream closed"),
        StreamBrokenError("stream broken"),
    ]

    for exc in exceptions_to_test:
        with pytest.raises(PyFFmpegAudioIOError) as exc_info:
            raise exc
        assert exc_info.value is exc


def test_ffmpeg_error_stderr_attribute() -> None:
    """Verify that FFmpegError properly preserves stderr."""
    err = FFmpegError("failed", stderr="error details from ffmpeg")
    assert err.stderr == "error details from ffmpeg"
    assert str(err) == "failed"


def test_functions_raise_audio_type_error() -> None:
    """Verify that calling functions with invalid types raises AudioTypeError."""
    with pytest.raises(AudioTypeError):
        decode(12345)  # type: ignore[arg-type]

    with pytest.raises(AudioTypeError):
        get_audio_info(12345)  # type: ignore[arg-type]
