"""Tests for AudioStreamReader."""

from __future__ import annotations

from pathlib import Path
from typing import Any, cast

import numpy as np
import pytest

from python_ffmpeg_audio_io import (
    PCM,
    AudioInfo,
    AudioStreamReader,
    FileReadError,
    PCMCodec,
    PCMFormat,
    PCMSampleRate,
    StreamClosedError,
    decode,
)


def test_stream_reader_properties() -> None:
    """Test AudioStreamReader properties and initialization."""
    sample_path = Path("samples/sample.mp3")
    with AudioStreamReader(
        sample_path, pcm_codec=PCMCodec.PCM_F32LE, chunk_frames=2048
    ) as reader:
        assert isinstance(reader.info, AudioInfo)
        assert reader.info.channels == 1
        assert reader.info.sample_rate == 44100
        assert reader.pcm_codec == PCMCodec.PCM_F32LE
        assert reader.pcm_format == PCMFormat.F32LE
        assert reader.sample_rate == PCMSampleRate.RATE_44K
        assert reader.chunk_frames == 2048
        assert reader.frame_size == 4  # f32 (4 bytes) * 1 channel
        assert not reader.closed

    assert reader.closed


def test_stream_reader_iteration_matches_decoder() -> None:
    """Verify that streaming read produces identical data to batch decode()."""
    sample_path = Path("samples/sample.mp3")

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
    sample_path = Path("samples/sample.mp3")
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
    sample_path = Path("samples/sample.mp3")
    with AudioStreamReader(
        sample_path, pcm_codec=PCMCodec.PCM_F32LE, chunk_frames=1024
    ) as reader:
        chunk = reader.read()
        assert chunk is not None
        arr = chunk.as_numpy()
        assert isinstance(arr, np.ndarray)
        assert arr.shape == (1024, 1)
        assert arr.dtype == np.float32


def test_stream_reader_closed_operations() -> None:
    """Test that operating on a closed reader raises StreamClosedError."""
    sample_path = Path("samples/sample.mp3")
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
    sample_path = Path("samples/sample.mp3")
    with AudioStreamReader(sample_path, chunk_frames=1024) as reader:
        chunk = reader.read()
        assert chunk is not None
        # Reader is closed on context exit without reading entire file

    assert reader.closed


def test_stream_reader_invalid_inputs(tmp_path: Path) -> None:
    """Test validation and error handling for invalid input parameters."""
    sample_path = Path("samples/sample.mp3")

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
