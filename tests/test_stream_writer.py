"""Tests for BaseAudioStreamWriter and derived stream writer classes."""

from __future__ import annotations

from pathlib import Path
from typing import Any, cast

import pytest

from python_ffmpeg_audio_io import (
    PCM,
    AACEncoderBitrate,
    AACEncoderMode,
    AACEncoderQualityLevel,
    AACStreamWriter,
    AIFFStreamWriter,
    AudioInfo,
    AudioStreamReader,
    AudioTypeError,
    BaseAudioStreamWriter,
    FileWriteError,
    FLACEncoderCompressionLevel,
    FLACStreamWriter,
    MP3EncoderBitrate,
    MP3EncoderMode,
    MP3EncoderQualityLevel,
    MP3StreamWriter,
    OpusEncoderApplication,
    OpusEncoderBitrate,
    OpusEncoderMode,
    OpusStreamWriter,
    PCMChannels,
    PCMCodec,
    PCMFormat,
    PCMSampleRate,
    StreamClosedError,
    WAVStreamWriter,
    get_audio_info,
)


@pytest.fixture
def sample_pcm() -> PCM:
    """Fixture to decode sample.mp3 into PCM for tests."""
    sample_path = Path("samples/sample.mp3")
    with AudioStreamReader(
        sample_path, pcm_codec=PCMCodec.PCM_F32LE, chunk_frames=4096
    ) as reader:
        chunks: list[PCM] = list(reader)

    all_data = b"".join(chunk.data for chunk in chunks)
    return PCM(
        data=all_data,
        format=PCMFormat.F32LE,
        sample_rate=PCMSampleRate.RATE_44K,
        channels=PCMChannels.MONO,
    )


def test_mp3_stream_writer_properties(tmp_path: Path) -> None:
    """Test MP3StreamWriter properties and default attributes."""
    out_file = tmp_path / "test.mp3"
    with MP3StreamWriter(
        out_file,
        sample_rate=PCMSampleRate.RATE_44K,
        channels=PCMChannels.STEREO,
        pcm_format=PCMFormat.F32LE,
        bitrate=MP3EncoderBitrate.Kbps_256,
        mode=MP3EncoderMode.CBR,
        quality=MP3EncoderQualityLevel.Quality_0,
    ) as writer:
        assert isinstance(writer, BaseAudioStreamWriter)
        assert writer.path == out_file
        assert writer.sample_rate == PCMSampleRate.RATE_44K
        assert writer.channels == PCMChannels.STEREO
        assert writer.pcm_format == PCMFormat.F32LE
        assert writer.frame_size == 8  # 4 bytes * 2 channels
        assert writer.bitrate == MP3EncoderBitrate.Kbps_256
        assert writer.mode == MP3EncoderMode.CBR
        assert writer.quality == MP3EncoderQualityLevel.Quality_0
        assert writer.codec == "libmp3lame"
        assert not writer.closed
        assert writer.frames_written == 0
        assert writer.bytes_written == 0

    assert writer.closed


def test_mp3_stream_writer_streaming(tmp_path: Path, sample_pcm: PCM) -> None:
    """Test streaming chunks to MP3StreamWriter and verify output."""
    out_file = tmp_path / "output.mp3"
    chunk_frames = 1024
    frame_size = sample_pcm.format.bytes_per_sample * sample_pcm.channels.value
    chunk_bytes = chunk_frames * frame_size

    total_frames = len(sample_pcm.data) // frame_size

    with MP3StreamWriter(
        out_file,
        sample_rate=sample_pcm.sample_rate,
        channels=sample_pcm.channels,
        pcm_format=sample_pcm.format,
    ) as writer:
        for offset in range(0, len(sample_pcm.data), chunk_bytes):
            chunk_data = sample_pcm.data[offset : offset + chunk_bytes]
            chunk = PCM(
                data=chunk_data,
                format=sample_pcm.format,
                sample_rate=sample_pcm.sample_rate,
                channels=sample_pcm.channels,
            )
            written = writer.write(chunk)
            assert written == len(chunk_data) // frame_size

    assert writer.frames_written == total_frames
    assert writer.bytes_written == len(sample_pcm.data)
    assert out_file.exists()
    assert out_file.stat().st_size > 0

    info = get_audio_info(out_file)
    assert isinstance(info, AudioInfo)
    assert info.sample_rate == 44100
    assert info.channels == 1
    assert abs(info.duration - 36.0) < 1.0


def test_stream_writer_write_bytes(tmp_path: Path, sample_pcm: PCM) -> None:
    """Test writing raw bytes with write_bytes and flush."""
    out_file = tmp_path / "output_bytes.mp3"

    with MP3StreamWriter(
        out_file,
        sample_rate=sample_pcm.sample_rate,
        channels=sample_pcm.channels,
        pcm_format=sample_pcm.format,
    ) as writer:
        written_bytes = writer.write_bytes(sample_pcm.data)
        assert written_bytes == len(sample_pcm.data)
        writer.flush()

    assert out_file.exists()
    assert out_file.stat().st_size > 0


def test_aac_stream_writer(tmp_path: Path, sample_pcm: PCM) -> None:
    """Test AACStreamWriter with CBR and VBR modes."""
    # CBR
    out_m4a = tmp_path / "output.m4a"
    with AACStreamWriter(
        out_m4a,
        sample_rate=sample_pcm.sample_rate,
        channels=sample_pcm.channels,
        pcm_format=sample_pcm.format,
        bitrate=AACEncoderBitrate.Kbps_128,
        mode=AACEncoderMode.CBR,
    ) as writer:
        assert writer.codec == "aac"
        writer.write(sample_pcm)

    assert out_m4a.exists()
    info = get_audio_info(out_m4a)
    assert info.codec_name == "aac"
    assert info.channels == 1

    # VBR
    out_aac = tmp_path / "output.aac"
    with AACStreamWriter(
        out_aac,
        sample_rate=sample_pcm.sample_rate,
        channels=sample_pcm.channels,
        pcm_format=sample_pcm.format,
        mode=AACEncoderMode.VBR,
        quality=AACEncoderQualityLevel.Quality_4,
    ) as writer:
        writer.write(sample_pcm)

    assert out_aac.exists()
    info_vbr = get_audio_info(out_aac)
    assert info_vbr.codec_name == "aac"


def test_aiff_stream_writer(tmp_path: Path, sample_pcm: PCM) -> None:
    """Test AIFFStreamWriter with PCM_S16BE codec."""
    out_aiff = tmp_path / "output.aiff"
    with AIFFStreamWriter(
        out_aiff,
        sample_rate=sample_pcm.sample_rate,
        channels=sample_pcm.channels,
        pcm_format=sample_pcm.format,
        codec=PCMCodec.PCM_S16BE,
    ) as writer:
        assert writer.codec == PCMCodec.PCM_S16BE
        writer.write(sample_pcm)

    assert out_aiff.exists()
    info = get_audio_info(out_aiff)
    assert info.format_name == "aiff"
    assert info.channels == 1


def test_wav_stream_writer(tmp_path: Path, sample_pcm: PCM) -> None:
    """Test WAVStreamWriter with various PCM codecs and file extensions."""
    # 1. Default (PCM_S16LE, .wav)
    out_wav = tmp_path / "output.wav"
    with WAVStreamWriter(
        out_wav,
        sample_rate=sample_pcm.sample_rate,
        channels=sample_pcm.channels,
        pcm_format=sample_pcm.format,
    ) as writer:
        assert writer.codec == PCMCodec.PCM_S16LE
        writer.write(sample_pcm)

    assert out_wav.exists()
    info = get_audio_info(out_wav)
    assert info.format_name == "wav"
    assert info.channels == 1
    assert info.sample_rate == 44100

    # 2. PCM_S24LE (.wav)
    out_wav24 = tmp_path / "output_s24.wav"
    with WAVStreamWriter(
        out_wav24,
        sample_rate=sample_pcm.sample_rate,
        channels=sample_pcm.channels,
        pcm_format=sample_pcm.format,
        codec=PCMCodec.PCM_S24LE,
    ) as writer:
        assert writer.codec == PCMCodec.PCM_S24LE
        writer.write(sample_pcm)

    assert out_wav24.exists()

    # 3. PCM_F32LE (.wave)
    out_wave_f32 = tmp_path / "output_f32.wave"
    with WAVStreamWriter(
        out_wave_f32,
        sample_rate=sample_pcm.sample_rate,
        channels=sample_pcm.channels,
        pcm_format=sample_pcm.format,
        codec=PCMCodec.PCM_F32LE,
    ) as writer:
        assert writer.codec == PCMCodec.PCM_F32LE
        writer.write(sample_pcm)

    assert out_wave_f32.exists()


def test_flac_stream_writer(tmp_path: Path, sample_pcm: PCM) -> None:
    """Test FLACStreamWriter with compression level."""
    out_flac = tmp_path / "output.flac"
    with FLACStreamWriter(
        out_flac,
        sample_rate=sample_pcm.sample_rate,
        channels=sample_pcm.channels,
        pcm_format=sample_pcm.format,
        compression_level=FLACEncoderCompressionLevel.Level_8,
    ) as writer:
        assert writer.codec == "flac"
        assert writer.compression_level == FLACEncoderCompressionLevel.Level_8
        writer.write(sample_pcm)

    assert out_flac.exists()
    info = get_audio_info(out_flac)
    assert info.codec_name == "flac"
    assert info.channels == 1


def test_opus_stream_writer(tmp_path: Path, sample_pcm: PCM) -> None:
    """Test OpusStreamWriter with various options."""
    out_opus = tmp_path / "output.opus"
    with OpusStreamWriter(
        out_opus,
        sample_rate=sample_pcm.sample_rate,
        channels=sample_pcm.channels,
        pcm_format=sample_pcm.format,
        bitrate=OpusEncoderBitrate.Kbps_96,
        mode=OpusEncoderMode.VBR,
        application=OpusEncoderApplication.AUDIO,
    ) as writer:
        assert writer.codec == "libopus"
        assert writer.bitrate == OpusEncoderBitrate.Kbps_96
        assert writer.mode == OpusEncoderMode.VBR
        assert writer.application == OpusEncoderApplication.AUDIO
        writer.write(sample_pcm)

    assert out_opus.exists()
    info = get_audio_info(out_opus)
    assert info.codec_name == "opus"


def test_piping_reader_to_writer(tmp_path: Path) -> None:
    """Test piping chunks directly from AudioStreamReader to MP3StreamWriter."""
    sample_path = Path("samples/sample.mp3")
    out_file = tmp_path / "piped.mp3"

    with AudioStreamReader(
        sample_path, pcm_codec=PCMCodec.PCM_F32LE, chunk_frames=2048
    ) as reader:
        with MP3StreamWriter(
            out_file,
            sample_rate=reader.sample_rate,
            channels=reader.channels,
            pcm_format=reader.pcm_format,
        ) as writer:
            for chunk in reader:
                writer.write(chunk)

    assert out_file.exists()
    info = get_audio_info(out_file)
    assert info.channels == 1
    assert abs(info.duration - 36.0) < 1.0


def test_stream_writer_int_sample_rate_and_channels_raises_type_error(
    tmp_path: Path,
) -> None:
    """Test initializing stream writer with int raises AudioTypeError."""
    out_file = tmp_path / "test_int.mp3"
    with pytest.raises(
        AudioTypeError,
        match="sample_rate must be an instance of PCMSampleRate",
    ):
        _ = MP3StreamWriter(
            out_file,
            sample_rate=cast(Any, 44100),
        )

    with pytest.raises(
        AudioTypeError,
        match="channels must be an instance of PCMChannels",
    ):
        _ = MP3StreamWriter(
            out_file,
            channels=cast(Any, 1),
        )


def test_stream_writer_closed_errors(tmp_path: Path, sample_pcm: PCM) -> None:
    """Test that operations on a closed stream writer raise StreamClosedError."""
    out_file = tmp_path / "test_closed.mp3"
    writer = MP3StreamWriter(
        out_file,
        sample_rate=sample_pcm.sample_rate,
        channels=sample_pcm.channels,
        pcm_format=sample_pcm.format,
    )
    writer.close()
    assert writer.closed

    # Second close is idempotent
    writer.close()

    with pytest.raises(StreamClosedError, match="Cannot write to a closed"):
        writer.write(sample_pcm)

    with pytest.raises(StreamClosedError, match="Cannot write to a closed"):
        writer.write_bytes(b"\x00" * writer.frame_size)

    with pytest.raises(StreamClosedError, match="Cannot flush a closed"):
        writer.flush()


def test_stream_writer_context_exception_cleanup(tmp_path: Path) -> None:
    """Test that exceptions raised within context propagate without secondary errors."""
    out_file = tmp_path / "test_error.mp3"
    writer = MP3StreamWriter(out_file)

    with pytest.raises(RuntimeError, match="intentional error"):
        with writer:
            raise RuntimeError("intentional error")

    assert writer.closed


def test_stream_writer_unaligned_data(tmp_path: Path) -> None:
    """Test that writing unaligned byte data raises ValueError."""
    out_file = tmp_path / "test_unaligned.mp3"
    with MP3StreamWriter(
        out_file,
        sample_rate=PCMSampleRate.RATE_44K,
        channels=PCMChannels.STEREO,
        pcm_format=PCMFormat.F32LE,
    ) as writer:
        # frame_size is 8 bytes. 5 bytes is unaligned.
        with pytest.raises(ValueError, match="not aligned to frame size"):
            writer.write_bytes(b"\x00" * 5)


def test_stream_writer_pcm_mismatch(tmp_path: Path, sample_pcm: PCM) -> None:
    """Test that writing PCM with mismatched format, sample_rate, or channels raises."""
    out_file = tmp_path / "test_mismatch.mp3"

    # Sample rate mismatch
    with MP3StreamWriter(
        out_file,
        sample_rate=PCMSampleRate.RATE_48K,
        channels=sample_pcm.channels,
        pcm_format=sample_pcm.format,
    ) as writer:
        with pytest.raises(ValueError, match="Sample rate mismatch"):
            writer.write(sample_pcm)

    # Channel count mismatch
    out_file2 = tmp_path / "test_mismatch2.mp3"
    with MP3StreamWriter(
        out_file2,
        sample_rate=sample_pcm.sample_rate,
        channels=PCMChannels.STEREO,
        pcm_format=sample_pcm.format,
    ) as writer:
        with pytest.raises(ValueError, match="Channel count mismatch"):
            writer.write(sample_pcm)

    # PCM format mismatch
    out_file3 = tmp_path / "test_mismatch3.mp3"
    with MP3StreamWriter(
        out_file3,
        sample_rate=sample_pcm.sample_rate,
        channels=sample_pcm.channels,
        pcm_format=PCMFormat.S16LE,
    ) as writer:
        with pytest.raises(ValueError, match="PCM format mismatch"):
            writer.write(sample_pcm)


def test_stream_writer_overwrite_error(tmp_path: Path) -> None:
    """Test that existing destination raises FileWriteError if overwrite=False."""
    existing_file = tmp_path / "existing.mp3"
    existing_file.write_bytes(b"dummy")

    with pytest.raises(FileWriteError, match="Output file already exists"):
        _ = MP3StreamWriter(existing_file, overwrite=False)

    # With overwrite=True, it succeeds
    with MP3StreamWriter(existing_file, overwrite=True) as writer:
        assert not writer.closed


def test_stream_writer_invalid_arguments(tmp_path: Path) -> None:
    """Test argument validation for invalid types and values."""
    # Invalid path
    with pytest.raises(TypeError, match="output_path must be a str or PathLike"):
        _ = MP3StreamWriter(cast(Any, 12345))

    # Invalid overwrite
    with pytest.raises(TypeError, match="overwrite must be a bool"):
        _ = MP3StreamWriter(tmp_path / "a.mp3", overwrite=cast(Any, "yes"))

    # Invalid extension
    with pytest.raises(ValueError, match="Unsupported output file extension"):
        _ = MP3StreamWriter(tmp_path / "a.wav")

    # Invalid sample_rate type
    with pytest.raises(
        TypeError,
        match="sample_rate must be an instance of PCMSampleRate",
    ):
        _ = MP3StreamWriter(tmp_path / "a.mp3", sample_rate=cast(Any, "44100"))

    # Invalid channels type
    with pytest.raises(
        TypeError,
        match="channels must be an instance of PCMChannels",
    ):
        _ = MP3StreamWriter(tmp_path / "a.mp3", channels=cast(Any, "stereo"))

    # Invalid pcm_format
    with pytest.raises(TypeError, match="pcm_format must be PCMFormat"):
        _ = MP3StreamWriter(tmp_path / "a.mp3", pcm_format=cast(Any, "f32le"))

    # Invalid encoder options
    with pytest.raises(TypeError, match="bitrate must be MP3EncoderBitrate"):
        _ = MP3StreamWriter(tmp_path / "a.mp3", bitrate=cast(Any, "192k"))

    with pytest.raises(TypeError, match="mode must be MP3EncoderMode"):
        _ = MP3StreamWriter(tmp_path / "a.mp3", mode=cast(Any, "CBR"))

    with pytest.raises(TypeError, match="quality must be MP3EncoderQualityLevel"):
        _ = MP3StreamWriter(tmp_path / "a.mp3", quality=cast(Any, 2))

    with pytest.raises(TypeError, match="codec must be an instance of PCMCodec"):
        _ = AIFFStreamWriter(tmp_path / "a.aiff", codec=cast(Any, "pcm_s16be"))

    with pytest.raises(TypeError, match="codec must be an instance of PCMCodec"):
        _ = WAVStreamWriter(tmp_path / "a.wav", codec=cast(Any, "pcm_s16le"))

    with pytest.raises(ValueError, match="Unsupported output file extension"):
        _ = WAVStreamWriter(tmp_path / "a.mp3")

    with pytest.raises(
        TypeError, match="compression_level must be FLACEncoderCompressionLevel"
    ):
        _ = FLACStreamWriter(tmp_path / "a.flac", compression_level=cast(Any, 5))

    with pytest.raises(TypeError, match="application must be OpusEncoderApplication"):
        _ = OpusStreamWriter(tmp_path / "a.opus", application=cast(Any, "audio"))
