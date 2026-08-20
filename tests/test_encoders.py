"""Comprehensive tests for python-ffmpeg-audio-io package."""

from __future__ import annotations

from os import PathLike
from pathlib import Path
from typing import Any, cast
from unittest.mock import patch

import pytest

from python_ffmpeg_audio_io.decoder import decode
from python_ffmpeg_audio_io.encoder.aac import (
    AACEncoder,
    AACEncoderBitrate,
    AACEncoderMode,
    AACEncoderQualityLevel,
)
from python_ffmpeg_audio_io.encoder.aiff import AIFFEncoder
from python_ffmpeg_audio_io.encoder.base import BaseAudioEncoder
from python_ffmpeg_audio_io.encoder.flac import (
    FLACEncoder,
    FLACEncoderCompressionLevel,
)
from python_ffmpeg_audio_io.encoder.mp3 import (
    MP3Encoder,
    MP3EncoderBitrate,
    MP3EncoderMode,
    MP3EncoderQualityLevel,
)
from python_ffmpeg_audio_io.encoder.opus import (
    OpusEncoder,
    OpusEncoderApplication,
    OpusEncoderBitrate,
    OpusEncoderMode,
)
from python_ffmpeg_audio_io.exceptions import (
    FileReadError,
    FileWriteError,
    PyFFmpegAudioIOError,
)
from python_ffmpeg_audio_io.ffprobe import (
    AudioInfo,
    FFprobeLogLevel,
    get_audio_info,
    run_ffprobe,
)
from python_ffmpeg_audio_io.pcm import (
    PCM,
    PCMChannels,
    PCMCodec,
    PCMFormat,
    PCMSampleRate,
)


def test_sample_exists() -> None:
    """Verify that sample audio file exists."""
    sample_path = Path("samples/sample.mp3")
    assert sample_path.exists(), f"Sample file not found at {sample_path}"


def test_ffprobe_on_sample() -> None:
    """Verify metadata extraction with ffprobe and get_audio_info."""
    sample_path = Path("samples/sample.mp3")
    info = get_audio_info(sample_path)

    assert isinstance(info, AudioInfo)
    assert info.sample_rate == 44100
    assert info.channels == 1
    assert abs(info.duration - 36.022857) < 0.1
    assert info.codec_name == "mp3"
    assert info.format_name == "mp3"
    assert info.size > 0
    assert info.bit_rate > 0

    raw_data = run_ffprobe(sample_path, log_level=FFprobeLogLevel.ERROR)
    assert "streams" in raw_data
    assert "format" in raw_data


def test_decoder_on_sample() -> None:
    """Verify decoding sample audio to PCM."""
    sample_path = Path("samples/sample.mp3")
    pcm = decode(sample_path, pcm_codec=PCMCodec.PCM_F32LE)

    assert isinstance(pcm, PCM)
    assert pcm.format == PCMFormat.F32LE
    assert pcm.sample_rate == PCMSampleRate.RATE_44K
    assert pcm.channels == PCMChannels.MONO
    assert len(pcm.data) > 0

    # Also test decoding to another codec (e.g. S16LE)
    pcm_s16 = decode(sample_path, pcm_codec=PCMCodec.PCM_S16LE)
    assert pcm_s16.format == PCMFormat.S16LE
    assert len(pcm_s16.data) > 0


def test_decoder_unsupported_metadata(tmp_path: Path) -> None:
    """Verify decoder raises PyFFmpegAudioIOError on unsupported
    channel or sample rate.
    """
    sample_path = Path("samples/sample.mp3")

    fake_info_bad_channels = AudioInfo(
        sample_rate=44100,
        sample_fmt="fltp",
        channels=99,
        duration=1.0,
        codec_name="mp3",
        format_name="mp3",
        format_long_name="MP3",
        size=1000,
        bit_rate=128000,
    )
    with patch(
        "python_ffmpeg_audio_io.decoder.get_audio_info",
        return_value=fake_info_bad_channels,
    ):
        with pytest.raises(
            PyFFmpegAudioIOError, match="Unsupported channel count '99'"
        ):
            _ = decode(sample_path)

    fake_info_bad_rate = AudioInfo(
        sample_rate=12345,
        sample_fmt="fltp",
        channels=2,
        duration=1.0,
        codec_name="mp3",
        format_name="mp3",
        format_long_name="MP3",
        size=1000,
        bit_rate=128000,
    )
    with patch(
        "python_ffmpeg_audio_io.decoder.get_audio_info", return_value=fake_info_bad_rate
    ):
        with pytest.raises(
            PyFFmpegAudioIOError, match="Unsupported sample rate '12345'"
        ):
            _ = decode(sample_path)


def test_encoders_instantiation_and_properties() -> None:
    """Test instantiation and property getters/setters for all encoders."""
    # 1. AAC Encoder
    aac_encoder = AACEncoder(
        bitrate=AACEncoderBitrate.Kbps_128,
        mode=AACEncoderMode.CBR,
        quality=AACEncoderQualityLevel.Quality_3,
    )
    assert aac_encoder.codec == "aac"
    assert aac_encoder.bitrate == AACEncoderBitrate.Kbps_128
    assert aac_encoder.mode == AACEncoderMode.CBR
    assert aac_encoder.quality == AACEncoderQualityLevel.Quality_3

    aac_encoder.bitrate = AACEncoderBitrate.Kbps_256
    assert aac_encoder.bitrate == AACEncoderBitrate.Kbps_256
    aac_encoder.mode = AACEncoderMode.VBR
    assert aac_encoder.mode == AACEncoderMode.VBR
    aac_encoder.quality = AACEncoderQualityLevel.Quality_5
    assert aac_encoder.quality == AACEncoderQualityLevel.Quality_5

    with pytest.raises(TypeError):
        _ = AACEncoder(bitrate=cast(Any, "invalid"))
    with pytest.raises(TypeError):
        _ = AACEncoder(mode=cast(Any, "invalid"))
    with pytest.raises(TypeError):
        _ = AACEncoder(quality=cast(Any, "invalid"))
    with pytest.raises(TypeError):
        aac_encoder.bitrate = cast(Any, "invalid")
    with pytest.raises(TypeError):
        aac_encoder.mode = cast(Any, "invalid")
    with pytest.raises(TypeError):
        aac_encoder.quality = cast(Any, "invalid")

    # 2. MP3 Encoder
    mp3_encoder = MP3Encoder(
        bitrate=MP3EncoderBitrate.Kbps_192,
        mode=MP3EncoderMode.CBR,
        quality=MP3EncoderQualityLevel.Quality_2,
    )
    assert mp3_encoder.codec == "libmp3lame"
    assert mp3_encoder.bitrate == MP3EncoderBitrate.Kbps_192
    assert mp3_encoder.mode == MP3EncoderMode.CBR
    assert mp3_encoder.quality == MP3EncoderQualityLevel.Quality_2

    mp3_encoder.bitrate = MP3EncoderBitrate.Kbps_320
    assert mp3_encoder.bitrate == MP3EncoderBitrate.Kbps_320
    mp3_encoder.mode = MP3EncoderMode.ABR
    assert mp3_encoder.mode == MP3EncoderMode.ABR
    mp3_encoder.quality = MP3EncoderQualityLevel.Quality_0
    assert mp3_encoder.quality == MP3EncoderQualityLevel.Quality_0

    with pytest.raises(TypeError):
        _ = MP3Encoder(bitrate=cast(Any, "invalid"))
    with pytest.raises(TypeError):
        _ = MP3Encoder(mode=cast(Any, "invalid"))
    with pytest.raises(TypeError):
        _ = MP3Encoder(quality=cast(Any, "invalid"))
    with pytest.raises(TypeError):
        mp3_encoder.bitrate = cast(Any, "invalid")
    with pytest.raises(TypeError):
        mp3_encoder.mode = cast(Any, "invalid")
    with pytest.raises(TypeError):
        mp3_encoder.quality = cast(Any, "invalid")

    # 3. AIFF Encoder
    aiff_encoder = AIFFEncoder(codec=PCMCodec.PCM_S16BE)
    assert aiff_encoder.codec == PCMCodec.PCM_S16BE
    aiff_encoder.codec = PCMCodec.PCM_S24BE
    assert aiff_encoder.codec == PCMCodec.PCM_S24BE

    with pytest.raises(TypeError):
        _ = AIFFEncoder(codec=cast(Any, "invalid"))
    with pytest.raises(TypeError):
        aiff_encoder.codec = cast(Any, "invalid")

    # 4. Opus Encoder
    opus_encoder = OpusEncoder(
        bitrate=OpusEncoderBitrate.Kbps_128,
        mode=OpusEncoderMode.VBR,
        application=OpusEncoderApplication.AUDIO,
    )
    assert opus_encoder.codec == "libopus"
    assert opus_encoder.bitrate == OpusEncoderBitrate.Kbps_128
    assert opus_encoder.mode == OpusEncoderMode.VBR
    assert opus_encoder.application == OpusEncoderApplication.AUDIO

    opus_encoder.bitrate = OpusEncoderBitrate.Kbps_256
    assert opus_encoder.bitrate == OpusEncoderBitrate.Kbps_256
    opus_encoder.mode = OpusEncoderMode.CBR
    assert opus_encoder.mode == OpusEncoderMode.CBR
    opus_encoder.application = OpusEncoderApplication.VOIP
    assert opus_encoder.application == OpusEncoderApplication.VOIP

    with pytest.raises(TypeError):
        _ = OpusEncoder(bitrate=cast(Any, "invalid"))
    with pytest.raises(TypeError):
        _ = OpusEncoder(mode=cast(Any, "invalid"))
    with pytest.raises(TypeError):
        _ = OpusEncoder(application=cast(Any, "invalid"))
    with pytest.raises(TypeError):
        opus_encoder.bitrate = cast(Any, "invalid")
    with pytest.raises(TypeError):
        opus_encoder.mode = cast(Any, "invalid")
    with pytest.raises(TypeError):
        opus_encoder.application = cast(Any, "invalid")

    # 5. FLAC Encoder
    flac_encoder = FLACEncoder(
        compression_level=FLACEncoderCompressionLevel.Level_5,
    )
    assert flac_encoder.codec == "flac"
    assert flac_encoder.compression_level == FLACEncoderCompressionLevel.Level_5

    flac_encoder.compression_level = FLACEncoderCompressionLevel.Level_8
    assert flac_encoder.compression_level == FLACEncoderCompressionLevel.Level_8

    with pytest.raises(TypeError):
        _ = FLACEncoder(compression_level=cast(Any, "invalid"))
    with pytest.raises(TypeError):
        flac_encoder.compression_level = cast(Any, "invalid")


def test_encode_mp3(tmp_path: Path) -> None:
    """Test actual encoding of PCM data to MP3 files with different modes."""
    sample_path = Path("samples/sample.mp3")
    pcm = decode(sample_path)

    # 1. CBR
    out_cbr = tmp_path / "test_cbr.mp3"
    encoder_cbr = MP3Encoder(
        bitrate=MP3EncoderBitrate.Kbps_128, mode=MP3EncoderMode.CBR
    )
    encoder_cbr(pcm, out_cbr)
    assert out_cbr.exists()
    assert out_cbr.stat().st_size > 0
    info_cbr = get_audio_info(out_cbr)
    assert info_cbr.channels == 1
    assert info_cbr.sample_rate == 44100

    # 2. ABR
    out_abr = tmp_path / "test_abr.mp3"
    encoder_abr = MP3Encoder(
        bitrate=MP3EncoderBitrate.Kbps_160, mode=MP3EncoderMode.ABR
    )
    encoder_abr(pcm, out_abr)
    assert out_abr.exists()

    # 3. VBR
    out_vbr = tmp_path / "test_vbr.mp3"
    encoder_vbr = MP3Encoder(
        quality=MP3EncoderQualityLevel.Quality_2, mode=MP3EncoderMode.VBR
    )
    encoder_vbr(pcm, out_vbr)
    assert out_vbr.exists()


def test_encode_aac(tmp_path: Path) -> None:
    """Test actual encoding of PCM data to AAC/M4A files."""
    sample_path = Path("samples/sample.mp3")
    pcm = decode(sample_path)

    # 1. CBR (.m4a)
    out_cbr = tmp_path / "test_cbr.m4a"
    encoder_cbr = AACEncoder(
        bitrate=AACEncoderBitrate.Kbps_128, mode=AACEncoderMode.CBR
    )
    encoder_cbr(pcm, out_cbr)
    assert out_cbr.exists()
    assert out_cbr.stat().st_size > 0
    info_cbr = get_audio_info(out_cbr)
    assert info_cbr.channels == 1
    assert info_cbr.sample_rate == 44100

    # 2. VBR (.aac)
    out_vbr = tmp_path / "test_vbr.aac"
    encoder_vbr = AACEncoder(
        quality=AACEncoderQualityLevel.Quality_5, mode=AACEncoderMode.VBR
    )
    encoder_vbr(pcm, out_vbr)
    assert out_vbr.exists()


def test_encode_aiff(tmp_path: Path) -> None:
    """Test actual encoding of PCM data to AIFF files."""
    sample_path = Path("samples/sample.mp3")
    pcm = decode(sample_path)

    # 1. S16BE (.aiff)
    out_s16 = tmp_path / "test_s16.aiff"
    encoder_s16 = AIFFEncoder(codec=PCMCodec.PCM_S16BE)
    encoder_s16(pcm, out_s16)
    assert out_s16.exists()
    assert out_s16.stat().st_size > 0
    info_s16 = get_audio_info(out_s16)
    assert info_s16.channels == 1
    assert info_s16.sample_rate == 44100

    # 2. S24BE (.aif)
    out_s24 = tmp_path / "test_s24.aif"
    encoder_s24 = AIFFEncoder(codec=PCMCodec.PCM_S24BE)
    encoder_s24(pcm, out_s24)
    assert out_s24.exists()


def test_encode_opus(tmp_path: Path) -> None:
    """Test actual encoding of PCM data to Opus files."""
    sample_path = Path("samples/sample.mp3")
    pcm = decode(sample_path)

    # 1. VBR (.opus)
    out_vbr = tmp_path / "test_vbr.opus"
    encoder_vbr = OpusEncoder(
        bitrate=OpusEncoderBitrate.Kbps_128,
        mode=OpusEncoderMode.VBR,
        application=OpusEncoderApplication.AUDIO,
    )
    encoder_vbr(pcm, out_vbr)
    assert out_vbr.exists()
    assert out_vbr.stat().st_size > 0
    info_vbr = get_audio_info(out_vbr)
    assert info_vbr.channels == 1
    assert info_vbr.codec_name == "opus"

    # Decode encoded opus back
    decoded_opus = decode(out_vbr)
    assert isinstance(decoded_opus, PCM)
    assert len(decoded_opus.data) > 0

    # 2. CBR (.ogg)
    out_cbr = tmp_path / "test_cbr.ogg"
    encoder_cbr = OpusEncoder(
        bitrate=OpusEncoderBitrate.Kbps_64,
        mode=OpusEncoderMode.CBR,
        application=OpusEncoderApplication.VOIP,
    )
    encoder_cbr(pcm, out_cbr)
    assert out_cbr.exists()

    # 3. CVBR (.opus)
    out_cvbr = tmp_path / "test_cvbr.opus"
    encoder_cvbr = OpusEncoder(
        bitrate=OpusEncoderBitrate.Kbps_192,
        mode=OpusEncoderMode.CVBR,
        application=OpusEncoderApplication.LOW_DELAY,
    )
    encoder_cvbr(pcm, out_cvbr)
    assert out_cvbr.exists()


def test_encode_flac(tmp_path: Path) -> None:
    """Test actual encoding of PCM data to FLAC files."""
    sample_path = Path("samples/sample.mp3")
    pcm = decode(sample_path)

    # 1. Compression level 5 (.flac)
    out_flac = tmp_path / "test_level5.flac"
    encoder_flac = FLACEncoder(
        compression_level=FLACEncoderCompressionLevel.Level_5,
    )
    encoder_flac(pcm, out_flac)
    assert out_flac.exists()
    assert out_flac.stat().st_size > 0
    info_flac = get_audio_info(out_flac)
    assert info_flac.channels == 1
    assert info_flac.sample_rate == 44100
    assert info_flac.codec_name == "flac"

    # Decode encoded flac back
    decoded_flac = decode(out_flac)
    assert isinstance(decoded_flac, PCM)
    assert len(decoded_flac.data) > 0

    # 2. Compression level 0 (.flac)
    out_flac0 = tmp_path / "test_level0.flac"
    encoder_flac0 = FLACEncoder(
        compression_level=FLACEncoderCompressionLevel.Level_0,
    )
    encoder_flac0(pcm, out_flac0)
    assert out_flac0.exists()

    # 3. Compression level 8 (.flac)
    out_flac8 = tmp_path / "test_level8.flac"
    encoder_flac8 = FLACEncoder(
        compression_level=FLACEncoderCompressionLevel.Level_8,
    )
    encoder_flac8(pcm, out_flac8)
    assert out_flac8.exists()


def test_invalid_inputs_and_error_handling(tmp_path: Path) -> None:
    """Test exception handling for invalid inputs."""
    encoder = MP3Encoder()
    valid_pcm = PCM(
        data=b"\x00" * 1024,
        format=PCMFormat.F32LE,
        sample_rate=PCMSampleRate.RATE_44K,
        channels=PCMChannels.STEREO,
    )

    # 1. Invalid pcm parameter type to encoder
    with pytest.raises(TypeError, match="Invalid PCM data type"):
        encoder(
            cast(Any, "not-PCM"),
            tmp_path / "out.mp3",
        )

    # 2. Invalid output file path type
    with pytest.raises(TypeError, match="output_path must be a str or PathLike"):
        encoder(valid_pcm, cast(Any, 12345))

    # 3. Invalid overwrite parameter type
    with pytest.raises(TypeError, match="overwrite must be a bool"):
        encoder(valid_pcm, tmp_path / "out.mp3", overwrite=cast(Any, "yes"))

    # 4. Invalid output file extension
    with pytest.raises(ValueError, match="Unsupported output file extension"):
        encoder(
            valid_pcm,
            tmp_path / "out.txt",
        )

    # 4b. Invalid extension for OpusEncoder
    opus_enc = OpusEncoder()
    with pytest.raises(ValueError, match="Unsupported output file extension"):
        opus_enc(valid_pcm, tmp_path / "out.mp3")

    # 4c. Invalid extension for FLACEncoder
    flac_enc = FLACEncoder()
    with pytest.raises(ValueError, match="Unsupported output file extension"):
        flac_enc(valid_pcm, tmp_path / "out.txt")

    # 5. File already exists and overwrite=False
    out_file = tmp_path / "existing.mp3"
    _ = out_file.write_bytes(b"dummy")
    with pytest.raises(FileWriteError, match="Output file already exists"):
        encoder(
            valid_pcm,
            out_file,
            overwrite=False,
        )

    # 6. File already exists and overwrite=True succeeds
    encoder(valid_pcm, out_file, overwrite=True)
    assert out_file.exists()

    # 7. Decoder with non-existent file
    non_existent = tmp_path / "does_not_exist.mp3"
    with pytest.raises(FileReadError, match="Audio file not found"):
        _ = decode(non_existent)

    # 8. Decoder with invalid path type
    with pytest.raises(TypeError, match="path must be a str or PathLike"):
        _ = decode(cast(Any, None))

    # 9. Decoder with invalid pcm_codec type
    with pytest.raises(TypeError, match="pcm_codec must be an instance of PCMCodec"):
        _ = decode(Path("samples/sample.mp3"), pcm_codec=cast(Any, "pcm_f32le"))

    # 10. FFprobe with non-existent file
    with pytest.raises(FileReadError, match="Audio file not found"):
        _ = get_audio_info(non_existent)

    # 11. FFprobe with invalid path type
    with pytest.raises(TypeError, match="file_path must be a str or PathLike"):
        _ = get_audio_info(cast(Any, None))

    # 12. run_ffprobe with invalid log_level type
    with pytest.raises(
        TypeError, match="log_level must be an instance of FFprobeLogLevel"
    ):
        _ = run_ffprobe(Path("samples/sample.mp3"), log_level=cast(Any, "error"))


def test_base_audio_encoder_direct_checks() -> None:
    """Test BaseAudioEncoder input checking methods directly."""

    class DummyEncoder(BaseAudioEncoder):
        def __call__(
            self,
            pcm: PCM,
            output_path: str | PathLike[str],
            overwrite: bool = False,
        ) -> None:
            pass

    dummy = DummyEncoder()
    # Invalid supported_formats type
    with pytest.raises(TypeError, match="supported_formats must be a Sequence of str"):
        dummy._check_output_path(
            "test.mp3", supported_formats=cast(Any, 123), overwrite=False
        )

    # Invalid codec_args type
    valid_pcm = PCM(
        data=b"\x00" * 4,
        format=PCMFormat.S16LE,
        sample_rate=PCMSampleRate.RATE_44K,
        channels=PCMChannels.STEREO,
    )
    with pytest.raises(TypeError, match="codec_args must be a Sequence of str"):
        dummy._run_ffmpeg_encode(
            codec_args=cast(Any, 123),
            pcm=valid_pcm,
            output_path=Path("out.mp3"),
            overwrite=False,
        )
