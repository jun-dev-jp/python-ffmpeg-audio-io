"""Unit tests for the decode() function."""

from __future__ import annotations

import subprocess
from pathlib import Path
from typing import Any, cast
from unittest.mock import patch

import pytest

from python_ffmpeg_audio_io import (
    PCM,
    AudioTypeError,
    AudioValueError,
    FFmpegError,
    FFmpegNotFoundError,
    FileReadError,
    MP3Encoder,
    PCMChannels,
    PCMCodec,
    PCMFormat,
    PCMSampleRate,
    decode,
)


def test_decode_default_parameters() -> None:
    """Test decode() with default parameters preserving original attributes."""
    sample_path = Path("samples/65_BPM93.mp3")
    pcm = decode(sample_path)

    assert isinstance(pcm, PCM)
    assert pcm.format == PCMFormat.F32LE
    assert pcm.sample_rate == PCMSampleRate.RATE_48K
    assert pcm.channels == PCMChannels.STEREO
    assert len(pcm.data) > 0


def test_decode_resampling() -> None:
    """Test decode() with target sample rate conversion (resampling)."""
    sample_path = Path("samples/65_BPM93.mp3")

    # Resample to 16kHz
    pcm_16k = decode(
        sample_path,
        sample_rate=PCMSampleRate.RATE_16K,
        duration=1.0,
    )
    assert pcm_16k.sample_rate == PCMSampleRate.RATE_16K
    # 1.0s * 16000 samples/s * 2 ch * 4 bytes/sample = 128000 bytes
    assert len(pcm_16k.data) == 128000

    # Resample to 48kHz
    pcm_48k = decode(
        sample_path,
        sample_rate=PCMSampleRate.RATE_48K,
        duration=1.0,
    )
    assert pcm_48k.sample_rate == PCMSampleRate.RATE_48K
    # 1.0s * 48000 samples/s * 2 ch * 4 bytes/sample = 384000 bytes
    assert len(pcm_48k.data) == 384000


def test_decode_channel_conversion(tmp_path: Path) -> None:
    """Test decode() with channel conversion (upmix and downmix)."""
    sample_path = Path("samples/65_BPM93.mp3")

    # Decode as stereo, then exercise stereo-to-mono downmixing.
    pcm_stereo = decode(
        sample_path,
        channels=PCMChannels.STEREO,
        duration=1.0,
    )
    assert pcm_stereo.channels == PCMChannels.STEREO
    # 1.0s * 48000 samples/s * 2 ch * 4 bytes/sample = 384000 bytes
    assert len(pcm_stereo.data) == 384000

    # Save stereo audio to test downmixing from stereo to mono
    stereo_file = tmp_path / "stereo.mp3"
    encoder = MP3Encoder()
    encoder(pcm_stereo, stereo_file)

    pcm_mono = decode(
        stereo_file,
        channels=PCMChannels.MONO,
        duration=1.0,
    )
    assert pcm_mono.channels == PCMChannels.MONO
    assert len(pcm_mono.data) == 192000


def test_decode_seek_and_duration() -> None:
    """Test decode() with start_time and duration interval specification."""
    sample_path = Path("samples/65_BPM93.mp3")

    # Decode with specific duration
    pcm_cut = decode(
        sample_path,
        duration=0.5,
        pcm_codec=PCMCodec.PCM_S16LE,
    )
    assert pcm_cut.format == PCMFormat.S16LE
    # 0.5s * 48000 * 2 ch * 2 bytes/sample = 96000 bytes
    assert len(pcm_cut.data) == 96000

    # Decode with start_time and duration
    pcm_seek_cut = decode(
        sample_path,
        start_time=1.5,
        duration=2.0,
        pcm_codec=PCMCodec.PCM_S16LE,
    )
    # 2.0s * 48000 * 2 ch * 2 bytes/sample = 384000 bytes
    assert len(pcm_seek_cut.data) == 384000

    # Combined resampling, channel conversion, seek, and duration
    pcm_combined = decode(
        sample_path,
        sample_rate=PCMSampleRate.RATE_16K,
        channels=PCMChannels.STEREO,
        start_time=2.0,
        duration=1.5,
        pcm_codec=PCMCodec.PCM_F32LE,
    )
    assert pcm_combined.sample_rate == PCMSampleRate.RATE_16K
    assert pcm_combined.channels == PCMChannels.STEREO
    # 1.5s * 16000 * 2 ch * 4 bytes/sample = 192000 bytes
    assert len(pcm_combined.data) == 192000


def test_decode_timecode() -> None:
    """Test decode() with string timecode specifications."""
    sample_path = Path("samples/65_BPM93.mp3")

    # Timecode format "MM:SS"
    pcm_mmss = decode(
        sample_path,
        start_time="00:01",
        duration="00:02",
        pcm_codec=PCMCodec.PCM_S16LE,
    )
    # 2.0s * 48000 * 2 ch * 2 bytes = 384000 bytes
    assert len(pcm_mmss.data) == 384000

    # Timecode format "HH:MM:SS.mmm"
    pcm_hhmmss = decode(
        sample_path,
        start_time="00:00:01.500",
        duration="00:00:00.500",
        pcm_codec=PCMCodec.PCM_S16LE,
    )
    # 0.5s * 48000 * 2 ch * 2 bytes = 96000 bytes
    assert len(pcm_hhmmss.data) == 96000

    # Output matches numeric float specification
    pcm_float = decode(
        sample_path,
        start_time=1.5,
        duration=0.5,
        pcm_codec=PCMCodec.PCM_S16LE,
    )
    assert pcm_hhmmss.data == pcm_float.data


def test_decode_seek_past_eof() -> None:
    """Test decode() seeking past end of audio file returns empty PCM."""
    sample_path = Path("samples/65_BPM93.mp3")
    pcm = decode(sample_path, start_time=100.0)

    assert isinstance(pcm, PCM)
    assert len(pcm.data) == 0


def test_decode_input_validation(tmp_path: Path) -> None:
    """Test argument validation for decode()."""
    sample_path = Path("samples/65_BPM93.mp3")

    # Invalid path type
    with pytest.raises(AudioTypeError, match="path must be a str or PathLike"):
        _ = decode(cast(Any, 12345))

    # Non-existent file
    non_existent = tmp_path / "not_found.mp3"
    with pytest.raises(FileReadError, match="Audio file not found"):
        _ = decode(non_existent)

    # Invalid pcm_codec type
    with pytest.raises(
        AudioTypeError, match="pcm_codec must be an instance of PCMCodec"
    ):
        _ = decode(sample_path, pcm_codec=cast(Any, "invalid"))

    # Invalid sample_rate type (including int)
    with pytest.raises(
        AudioTypeError,
        match="sample_rate must be an instance of PCMSampleRate or None",
    ):
        _ = decode(sample_path, sample_rate=cast(Any, 44100))

    with pytest.raises(
        AudioTypeError,
        match="sample_rate must be an instance of PCMSampleRate or None",
    ):
        _ = decode(sample_path, sample_rate=cast(Any, "44100"))

    with pytest.raises(
        AudioTypeError,
        match="sample_rate must be an instance of PCMSampleRate or None",
    ):
        _ = decode(sample_path, sample_rate=cast(Any, True))

    # Invalid channels type (including int)
    with pytest.raises(
        AudioTypeError,
        match="channels must be an instance of PCMChannels or None",
    ):
        _ = decode(sample_path, channels=cast(Any, 2))

    with pytest.raises(
        AudioTypeError,
        match="channels must be an instance of PCMChannels or None",
    ):
        _ = decode(sample_path, channels=cast(Any, "stereo"))

    with pytest.raises(
        AudioTypeError,
        match="channels must be an instance of PCMChannels or None",
    ):
        _ = decode(sample_path, channels=cast(Any, True))

    # Invalid start_time type
    with pytest.raises(
        AudioTypeError, match="start_time must be a float, int, str, or None"
    ):
        _ = decode(sample_path, start_time=cast(Any, []))

    with pytest.raises(
        AudioTypeError, match="start_time must be a float, int, str, or None"
    ):
        _ = decode(sample_path, start_time=cast(Any, True))

    # Invalid start_time value
    with pytest.raises(AudioValueError, match="start_time must be non-negative"):
        _ = decode(sample_path, start_time=-1.0)

    with pytest.raises(AudioValueError, match="start_time must be a finite number"):
        _ = decode(sample_path, start_time=float("nan"))

    with pytest.raises(AudioValueError, match="start_time must be a finite number"):
        _ = decode(sample_path, start_time=float("inf"))

    # Invalid start_time timecode strings
    with pytest.raises(AudioValueError, match="Timecode string cannot be empty"):
        _ = decode(sample_path, start_time="")

    with pytest.raises(AudioValueError, match="Invalid timecode string"):
        _ = decode(sample_path, start_time="invalid")

    with pytest.raises(AudioValueError, match="Minutes must be in range"):
        _ = decode(sample_path, start_time="00:60:00")

    with pytest.raises(AudioValueError, match="Seconds must be in range"):
        _ = decode(sample_path, start_time="00:00:60")

    with pytest.raises(AudioValueError, match="Minutes cannot be negative"):
        _ = decode(sample_path, start_time="-01:00")

    # Invalid duration type
    with pytest.raises(
        AudioTypeError, match="duration must be a float, int, str, or None"
    ):
        _ = decode(sample_path, duration=cast(Any, {}))

    with pytest.raises(
        AudioTypeError, match="duration must be a float, int, str, or None"
    ):
        _ = decode(sample_path, duration=cast(Any, False))

    # Invalid duration value
    with pytest.raises(AudioValueError, match="duration must be positive"):
        _ = decode(sample_path, duration=0)

    with pytest.raises(AudioValueError, match="duration must be positive"):
        _ = decode(sample_path, duration=-1.5)

    with pytest.raises(AudioValueError, match="duration must be a finite number"):
        _ = decode(sample_path, duration=float("nan"))

    with pytest.raises(AudioValueError, match="duration must be a finite number"):
        _ = decode(sample_path, duration=float("inf"))

    # Invalid duration timecode strings
    with pytest.raises(AudioValueError, match="duration must be positive"):
        _ = decode(sample_path, duration="00:00:00")

    with pytest.raises(AudioValueError, match="Invalid timecode string"):
        _ = decode(sample_path, duration="not_a_time")

    with pytest.raises(AudioValueError, match="duration must be a finite number"):
        _ = decode(sample_path, duration=float("inf"))


def test_decode_ffmpeg_not_found() -> None:
    """Test that FileNotFoundError when running FFmpeg raises FFmpegNotFoundError."""
    sample_path = Path("samples/65_BPM93.mp3")
    with patch(
        "python_ffmpeg_audio_io.decoder.subprocess.run",
        side_effect=FileNotFoundError("ffmpeg not found"),
    ):
        with pytest.raises(FFmpegNotFoundError, match="ffmpeg executable not found"):
            _ = decode(
                sample_path,
                sample_rate=PCMSampleRate.RATE_44K,
                channels=PCMChannels.MONO,
            )


def test_decode_oserror() -> None:
    """Test that generic OSError when running FFmpeg raises FFmpegError."""
    sample_path = Path("samples/65_BPM93.mp3")
    with patch(
        "python_ffmpeg_audio_io.decoder.subprocess.run",
        side_effect=OSError(13, "Permission denied"),
    ):
        with pytest.raises(FFmpegError, match="Failed to start ffmpeg process"):
            _ = decode(
                sample_path,
                sample_rate=PCMSampleRate.RATE_44K,
                channels=PCMChannels.MONO,
            )


def test_decode_nostdin_and_devnull() -> None:
    """Test that decode invokes FFmpeg with -nostdin and stdin=subprocess.DEVNULL."""
    sample_path = Path("samples/65_BPM93.mp3")
    mock_result = subprocess.CompletedProcess(
        args=[],
        returncode=0,
        stdout=b"\x00\x00\x00\x00",
        stderr=b"",
    )
    with patch(
        "python_ffmpeg_audio_io.decoder.subprocess.run",
        return_value=mock_result,
    ) as mock_run:
        _ = decode(
            sample_path,
            sample_rate=PCMSampleRate.RATE_44K,
            channels=PCMChannels.MONO,
        )
        cmd = mock_run.call_args[0][0]
        assert "-nostdin" in cmd
        assert mock_run.call_args[1].get("stdin") == subprocess.DEVNULL
