"""Tests for AudioStreamReader."""

from __future__ import annotations

import io
import subprocess
import time
from pathlib import Path
from typing import Any, cast
from unittest.mock import MagicMock, patch

import numpy as np
import pytest

from python_ffmpeg_audio_io import (
    PCM,
    AudioInfo,
    AudioStreamReader,
    FFmpegError,
    FFmpegNotFoundError,
    FileReadError,
    PCMChannels,
    PCMCodec,
    PCMFormat,
    PCMSampleRate,
    StreamBrokenError,
    StreamClosedError,
    decode,
)


def test_stream_reader_properties() -> None:
    """Test AudioStreamReader properties and initialization."""
    sample_path = Path("samples/65_BPM93.mp3")
    with AudioStreamReader(
        sample_path, pcm_codec=PCMCodec.PCM_F32LE, chunk_frames=2048
    ) as reader:
        assert isinstance(reader.info, AudioInfo)
        assert reader.info.channels == 2
        assert reader.info.sample_rate == 48000
        assert reader.pcm_codec == PCMCodec.PCM_F32LE
        assert reader.pcm_format == PCMFormat.F32LE
        assert reader.sample_rate == PCMSampleRate.RATE_48K
        assert reader.chunk_frames == 2048
        assert reader.frame_size == 8  # f32 (4 bytes) * 2 channels
        assert not reader.closed

    assert reader.closed


def test_stream_reader_iteration_matches_decoder() -> None:
    """Verify that streaming read produces identical data to batch decode()."""
    sample_path = Path("samples/65_BPM93.mp3")

    # Full decode using batch decoder
    decoded = decode(sample_path, pcm_codec=PCMCodec.PCM_S16LE)

    # Stream decode
    chunks: list[PCM] = []
    with AudioStreamReader(
        sample_path, pcm_codec=PCMCodec.PCM_S16LE, chunk_frames=4096
    ) as reader:
        for chunk in reader:
            assert isinstance(chunk, PCM)
            assert chunk.format == PCMFormat.S16LE
            chunks.append(chunk)

    total_streamed_bytes = b"".join(chunk.data for chunk in chunks)
    assert total_streamed_bytes == decoded.data


def test_stream_reader_read_method() -> None:
    """Test manual read() and read_bytes() methods."""
    sample_path = Path("samples/65_BPM93.mp3")
    with AudioStreamReader(
        sample_path, pcm_codec=PCMCodec.PCM_F32LE, chunk_frames=1024
    ) as reader:
        # Default frame read
        chunk1 = reader.read()
        assert chunk1 is not None
        assert len(chunk1.data) == 1024 * reader.frame_size

        # Custom frame read
        chunk2 = reader.read(frames=512)
        assert chunk2 is not None
        assert len(chunk2.data) == 512 * reader.frame_size

        # Raw bytes read
        raw = reader.read_bytes(frames=256)
        assert isinstance(raw, bytes)
        assert len(raw) == 256 * reader.frame_size


def test_stream_reader_as_numpy() -> None:
    """Test converting streamed PCM chunks to NumPy arrays."""
    sample_path = Path("samples/65_BPM93.mp3")
    with AudioStreamReader(
        sample_path, pcm_codec=PCMCodec.PCM_F32LE, chunk_frames=1024
    ) as reader:
        chunk = reader.read()
        assert chunk is not None
        arr = chunk.as_numpy()
        assert isinstance(arr, np.ndarray)
        assert arr.shape == (1024, 2)
        assert arr.dtype == np.float32


def test_stream_reader_closed_operations() -> None:
    """Test that operating on a closed reader raises StreamClosedError."""
    sample_path = Path("samples/65_BPM93.mp3")
    reader = AudioStreamReader(sample_path)
    reader.close()
    assert reader.closed

    # Second close should be a no-op
    reader.close()

    with pytest.raises(
        StreamClosedError, match="Cannot read from a closed AudioStreamReader"
    ):
        _ = reader.read()


def test_stream_reader_early_close() -> None:
    """Test closing reader before reading the full file."""
    sample_path = Path("samples/65_BPM93.mp3")
    with AudioStreamReader(sample_path, chunk_frames=1024) as reader:
        chunk = reader.read()
        assert chunk is not None
        # Reader is closed on context exit without reading entire file

    assert reader.closed


def test_stream_reader_invalid_inputs(tmp_path: Path) -> None:
    """Test validation and error handling for invalid input parameters."""
    sample_path = Path("samples/65_BPM93.mp3")

    # Invalid path type
    with pytest.raises(TypeError, match="path must be a str or PathLike"):
        _ = AudioStreamReader(cast(Any, 12345))

    # Non-existent file
    non_existent = tmp_path / "not_found.mp3"
    with pytest.raises(FileReadError, match="Audio file not found"):
        _ = AudioStreamReader(non_existent)

    # Invalid pcm_codec type
    with pytest.raises(TypeError, match="pcm_codec must be an instance of PCMCodec"):
        _ = AudioStreamReader(sample_path, pcm_codec=cast(Any, "invalid"))

    # Invalid chunk_frames type or value
    with pytest.raises(TypeError, match="chunk_frames must be an int"):
        _ = AudioStreamReader(sample_path, chunk_frames=cast(Any, "1024"))

    with pytest.raises(TypeError, match="chunk_frames must be an int"):
        _ = AudioStreamReader(sample_path, chunk_frames=cast(Any, True))

    with pytest.raises(ValueError, match="chunk_frames must be positive"):
        _ = AudioStreamReader(sample_path, chunk_frames=0)

    with pytest.raises(ValueError, match="chunk_frames must be positive"):
        _ = AudioStreamReader(sample_path, chunk_frames=-10)

    with AudioStreamReader(sample_path) as reader:
        with pytest.raises(TypeError, match="frames must be an int"):
            _ = reader.read(frames=cast(Any, "512"))
        with pytest.raises(ValueError, match="frames must be positive"):
            _ = reader.read(frames=0)


def test_stream_reader_resampling_and_channels() -> None:
    """Test AudioStreamReader with resampling and channel conversion."""
    sample_path = Path("samples/65_BPM93.mp3")

    with AudioStreamReader(
        sample_path,
        pcm_codec=PCMCodec.PCM_S16LE,
        sample_rate=PCMSampleRate.RATE_16K,
        channels=PCMChannels.STEREO,
        chunk_frames=1024,
        duration=1.0,
    ) as reader:
        assert reader.sample_rate == PCMSampleRate.RATE_16K
        assert reader.channels == PCMChannels.STEREO
        assert reader.pcm_format == PCMFormat.S16LE
        # 2 bytes/sample * 2 channels = 4 bytes/frame
        assert reader.frame_size == 4
        assert reader.duration == 1.0

        chunks: list[PCM] = list(reader)
        total_bytes = b"".join(chunk.data for chunk in chunks)
        # 1.0s * 16000 * 2 ch * 2 bytes = 64000 bytes
        assert len(total_bytes) == 64000


def test_stream_reader_seek_and_duration_matches_decoder() -> None:
    """Verify AudioStreamReader output matches decode() with seek and duration."""
    sample_path = Path("samples/65_BPM93.mp3")

    decoded = decode(
        sample_path,
        pcm_codec=PCMCodec.PCM_F32LE,
        sample_rate=PCMSampleRate.RATE_48K,
        channels=PCMChannels.STEREO,
        start_time=1.0,
        duration=2.0,
    )

    with AudioStreamReader(
        sample_path,
        pcm_codec=PCMCodec.PCM_F32LE,
        sample_rate=PCMSampleRate.RATE_48K,
        channels=PCMChannels.STEREO,
        start_time=1.0,
        duration=2.0,
        chunk_frames=2048,
    ) as reader:
        assert reader.start_time == 1.0
        assert reader.duration == 2.0
        streamed_bytes = b"".join(chunk.data for chunk in reader)

    assert streamed_bytes == decoded.data


def test_stream_reader_timecode() -> None:
    """Test AudioStreamReader with string timecode parameters."""
    sample_path = Path("samples/65_BPM93.mp3")

    with AudioStreamReader(
        sample_path,
        start_time="00:00:01",
        duration="00:00:01.500",
        chunk_frames=1024,
    ) as reader:
        assert reader.start_time == 1.0
        assert reader.duration == 1.5
        chunks = list(reader)
        total_bytes = b"".join(chunk.data for chunk in chunks)
        # 1.5s * 48000 * 2 ch * 4 bytes = 576000 bytes
        assert len(total_bytes) == 576000


def test_stream_reader_invalid_new_parameters() -> None:
    """Test input validation for new parameters in AudioStreamReader."""
    sample_path = Path("samples/65_BPM93.mp3")

    # sample_rate validation (including int)
    with pytest.raises(
        TypeError,
        match="sample_rate must be an instance of PCMSampleRate or None",
    ):
        _ = AudioStreamReader(sample_path, sample_rate=cast(Any, 44100))

    with pytest.raises(
        TypeError,
        match="sample_rate must be an instance of PCMSampleRate or None",
    ):
        _ = AudioStreamReader(sample_path, sample_rate=cast(Any, "44100"))

    with pytest.raises(
        TypeError,
        match="sample_rate must be an instance of PCMSampleRate or None",
    ):
        _ = AudioStreamReader(sample_path, sample_rate=cast(Any, True))

    # channels validation (including int)
    with pytest.raises(
        TypeError,
        match="channels must be an instance of PCMChannels or None",
    ):
        _ = AudioStreamReader(sample_path, channels=cast(Any, 2))

    with pytest.raises(
        TypeError,
        match="channels must be an instance of PCMChannels or None",
    ):
        _ = AudioStreamReader(sample_path, channels=cast(Any, "2"))

    with pytest.raises(
        TypeError,
        match="channels must be an instance of PCMChannels or None",
    ):
        _ = AudioStreamReader(sample_path, channels=cast(Any, True))

    # start_time validation
    with pytest.raises(
        TypeError, match="start_time must be a float, int, str, or None"
    ):
        _ = AudioStreamReader(sample_path, start_time=cast(Any, []))

    with pytest.raises(
        TypeError, match="start_time must be a float, int, str, or None"
    ):
        _ = AudioStreamReader(sample_path, start_time=cast(Any, False))

    with pytest.raises(ValueError, match="start_time must be non-negative"):
        _ = AudioStreamReader(sample_path, start_time=-1.0)

    with pytest.raises(ValueError, match="start_time must be a finite number"):
        _ = AudioStreamReader(sample_path, start_time=float("nan"))

    with pytest.raises(ValueError, match="Invalid timecode string"):
        _ = AudioStreamReader(sample_path, start_time="bad_timecode")

    # duration validation
    with pytest.raises(TypeError, match="duration must be a float, int, str, or None"):
        _ = AudioStreamReader(sample_path, duration=cast(Any, {}))

    with pytest.raises(TypeError, match="duration must be a float, int, str, or None"):
        _ = AudioStreamReader(sample_path, duration=cast(Any, True))

    with pytest.raises(ValueError, match="duration must be positive"):
        _ = AudioStreamReader(sample_path, duration=0)

    with pytest.raises(ValueError, match="duration must be positive"):
        _ = AudioStreamReader(sample_path, duration=-2.0)

    with pytest.raises(ValueError, match="duration must be a finite number"):
        _ = AudioStreamReader(sample_path, duration=float("inf"))

    with pytest.raises(ValueError, match="duration must be positive"):
        _ = AudioStreamReader(sample_path, duration="00:00:00")


@pytest.fixture
def dummy_audio_info() -> AudioInfo:
    """Fixture providing dummy AudioInfo for mocking."""
    return AudioInfo(
        sample_rate=44100,
        sample_fmt="fltp",
        channels=1,
        duration=1.0,
        codec_name="mp3",
        format_name="mp3",
        format_long_name="MP3",
        size=1000,
        bit_rate=128000,
    )


def test_stream_reader_ffmpeg_not_found(dummy_audio_info: AudioInfo) -> None:
    """Test that FileNotFoundError when spawning FFmpeg raises FFmpegNotFoundError."""
    sample_path = Path("samples/65_BPM93.mp3")
    with (
        patch(
            "python_ffmpeg_audio_io.stream_reader.get_audio_info",
            return_value=dummy_audio_info,
        ),
        patch(
            "python_ffmpeg_audio_io.stream_reader.subprocess.Popen",
            side_effect=FileNotFoundError("ffmpeg not found"),
        ),
    ):
        with pytest.raises(FFmpegNotFoundError, match="ffmpeg executable not found"):
            _ = AudioStreamReader(sample_path)


def test_stream_reader_oserror(dummy_audio_info: AudioInfo) -> None:
    """Test that generic OSError when spawning FFmpeg raises FFmpegError."""
    sample_path = Path("samples/65_BPM93.mp3")
    with (
        patch(
            "python_ffmpeg_audio_io.stream_reader.get_audio_info",
            return_value=dummy_audio_info,
        ),
        patch(
            "python_ffmpeg_audio_io.stream_reader.subprocess.Popen",
            side_effect=OSError(13, "Permission denied"),
        ),
    ):
        with pytest.raises(FFmpegError, match="Failed to start ffmpeg process"):
            _ = AudioStreamReader(sample_path)


def test_stream_reader_nostdin_and_devnull(dummy_audio_info: AudioInfo) -> None:
    """Test that FFmpeg is invoked with -nostdin and stdin=subprocess.DEVNULL."""
    sample_path = Path("samples/65_BPM93.mp3")
    with (
        patch(
            "python_ffmpeg_audio_io.stream_reader.get_audio_info",
            return_value=dummy_audio_info,
        ),
        patch("python_ffmpeg_audio_io.stream_reader.subprocess.Popen") as mock_popen,
    ):
        mock_proc = MagicMock()
        mock_proc.stdout = io.BytesIO(b"")
        mock_proc.stderr = io.BytesIO(b"")
        mock_proc.poll.return_value = 0
        mock_proc.wait.return_value = 0
        mock_popen.return_value = mock_proc

        with AudioStreamReader(sample_path) as reader:
            _ = reader.read()

        cmd = mock_popen.call_args[0][0]
        assert "-nostdin" in cmd
        assert mock_popen.call_args[1].get("stdin") == subprocess.DEVNULL


def test_stream_reader_large_stderr_drain_no_deadlock(
    dummy_audio_info: AudioInfo,
) -> None:
    """Test that background thread drains large stderr without deadlock."""
    sample_path = Path("samples/65_BPM93.mp3")
    # Generate 128KB of stderr data (exceeding typical 64KB pipe buffer)
    large_stderr = b"A" * (128 * 1024)
    # Output 1 frame of PCM data (4 bytes)
    mock_stdout_data = b"\x00\x00\x00\x00"

    with (
        patch(
            "python_ffmpeg_audio_io.stream_reader.get_audio_info",
            return_value=dummy_audio_info,
        ),
        patch("python_ffmpeg_audio_io.stream_reader.subprocess.Popen") as mock_popen,
    ):
        mock_proc = MagicMock()
        mock_proc.stdout = io.BytesIO(mock_stdout_data)
        mock_proc.stderr = io.BytesIO(large_stderr)
        mock_proc.poll.return_value = 0
        mock_proc.wait.return_value = 0
        mock_popen.return_value = mock_proc

        with AudioStreamReader(sample_path, chunk_frames=1) as reader:
            chunk = reader.read()
            assert chunk is not None
            assert len(chunk.data) == 4

            # Give thread a moment to finish draining
            time.sleep(0.05)
            # Total buffered bytes must be bounded by _stderr_max_bytes
            assert reader._stderr_total_bytes <= reader._stderr_max_bytes

            eof_chunk = reader.read()
            assert eof_chunk is None


def test_stream_reader_eof_race_condition_error_detection(
    dummy_audio_info: AudioInfo,
) -> None:
    """Test that process terminating with error at EOF is detected via wait().

    Simulates the race condition where poll() would return None right after
    stdout reaches EOF, but wait() returns exit code 1 with an error on stderr.
    """
    sample_path = Path("samples/65_BPM93.mp3")
    error_msg = b"Decoder error occurred at end of file"

    with (
        patch(
            "python_ffmpeg_audio_io.stream_reader.get_audio_info",
            return_value=dummy_audio_info,
        ),
        patch("python_ffmpeg_audio_io.stream_reader.subprocess.Popen") as mock_popen,
    ):
        mock_proc = MagicMock()
        mock_proc.stdout = io.BytesIO(b"")
        mock_proc.stderr = io.BytesIO(error_msg)
        # poll() returns None simulates process still terminating
        mock_proc.poll.return_value = None
        # wait() completes and reveals exit code 1
        mock_proc.wait.return_value = 1
        mock_popen.return_value = mock_proc

        with AudioStreamReader(sample_path) as reader:
            with pytest.raises(FFmpegError) as exc_info:
                _ = reader.read()

            assert exc_info.value.stderr == "Decoder error occurred at end of file"
            assert "terminated unexpectedly with code 1" in str(exc_info.value)


def test_stream_reader_unaligned_data(dummy_audio_info: AudioInfo) -> None:
    """Test that stream ending with unaligned data raises StreamBrokenError."""
    sample_path = Path("samples/65_BPM93.mp3")
    unaligned_bytes = b"\x00\x00\x00"  # 3 bytes, but frame_size is 4

    with (
        patch(
            "python_ffmpeg_audio_io.stream_reader.get_audio_info",
            return_value=dummy_audio_info,
        ),
        patch("python_ffmpeg_audio_io.stream_reader.subprocess.Popen") as mock_popen,
    ):
        mock_proc = MagicMock()
        mock_proc.stdout = io.BytesIO(unaligned_bytes)
        mock_proc.stderr = io.BytesIO(b"corrupt packet")
        mock_proc.poll.return_value = 0
        mock_proc.wait.return_value = 0
        mock_popen.return_value = mock_proc

        with AudioStreamReader(sample_path) as reader:
            with pytest.raises(StreamBrokenError) as exc_info:
                _ = reader.read()
            assert "unaligned data" in str(exc_info.value)
            assert exc_info.value.stderr == "corrupt packet"


def test_stream_reader_stdout_broken_pipe(dummy_audio_info: AudioInfo) -> None:
    """Test that BrokenPipeError on stdout read raises StreamBrokenError."""
    sample_path = Path("samples/65_BPM93.mp3")

    mock_stdout = MagicMock()
    mock_stdout.read.side_effect = BrokenPipeError("Pipe broken")

    with (
        patch(
            "python_ffmpeg_audio_io.stream_reader.get_audio_info",
            return_value=dummy_audio_info,
        ),
        patch("python_ffmpeg_audio_io.stream_reader.subprocess.Popen") as mock_popen,
    ):
        mock_proc = MagicMock()
        mock_proc.stdout = mock_stdout
        mock_proc.stderr = io.BytesIO(b"broken pipe details")
        mock_proc.poll.return_value = 1
        mock_proc.wait.return_value = 1
        mock_popen.return_value = mock_proc

        with AudioStreamReader(sample_path) as reader:
            with pytest.raises(StreamBrokenError) as exc_info:
                _ = reader.read()
            assert exc_info.value.stderr == "broken pipe details"


def test_stream_reader_subsequent_reads_after_eof() -> None:
    """Test that repeated read() calls after EOF continue to return None."""
    sample_path = Path("samples/65_BPM93.mp3")
    with AudioStreamReader(sample_path, duration=0.1) as reader:
        # Drain all chunks
        for _ in reader:
            pass

        # Further reads return None
        assert reader.read() is None
        assert reader.read() is None
        assert reader.read_bytes() == b""
