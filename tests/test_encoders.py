"""Tests for python-ffmpeg-audio-io package."""

from __future__ import annotations

from pathlib import Path

import pytest

from python_ffmpeg_audio_io.decoder import decode_to_PCM_F32LE_with_ffmpeg
from python_ffmpeg_audio_io.encoder.aac import (
    AACEncoder,
    AACEncoderBitrate,
    AACEncoderMode,
)
from python_ffmpeg_audio_io.encoder.aiff import AIFFEncoder
from python_ffmpeg_audio_io.encoder.mp3 import (
    MP3Encoder,
    MP3EncoderBitrate,
    MP3EncoderMode,
)
from python_ffmpeg_audio_io.ffprobe import get_audio_info_from_ffprobe


def test_sample_exists() -> None:
    sample_path = Path("samples/sample.mp3")
    assert sample_path.exists(), f"Sample file not found at {sample_path}"


def test_ffprobe_on_sample() -> None:
    sample_path = Path("samples/sample.mp3")
    if not sample_path.exists():
        return
    info = get_audio_info_from_ffprobe(sample_path)
    assert info.sample_rate == 44100
    assert info.channels  == 1
    assert info.duration == 36.022857


def test_encoders_instantiation() -> None:
    aac_encoder = AACEncoder(
        bitrate=AACEncoderBitrate.Kbps_128, mode=AACEncoderMode.CBR
    )
    assert aac_encoder.bitrate == AACEncoderBitrate.Kbps_128
    assert aac_encoder.mode == AACEncoderMode.CBR

    mp3_encoder = MP3Encoder(
        bitrate=MP3EncoderBitrate.Kbps_192, mode=MP3EncoderMode.CBR
    )
    assert mp3_encoder.bitrate == MP3EncoderBitrate.Kbps_192
    assert mp3_encoder.mode == MP3EncoderMode.CBR

    aiff_encoder = AIFFEncoder()
    assert aiff_encoder.codec.value == "pcm_s16be"


def test_invalid_inputs_and_error_handling(tmp_path: Path) -> None:
    """Test exception handling for invalid inputs across encoder, decoder, and ffprobe."""
    encoder = MP3Encoder()
    dummy_pcm = b"\x00" * 1024

    # 1. Invalid pcm_data type
    with pytest.raises(TypeError, match="Invalid PCM data type"):
        encoder(
            "not-bytes",  # type: ignore
            None,  # type: ignore
            None,  # type: ignore
            None,  # type: ignore
            tmp_path / "out.mp3",
        )

    # 2. Invalid output file extension
    from python_ffmpeg_audio_io.pcm import PCMChannels, PCMFormat, PCMSampleRate

    with pytest.raises(ValueError, match="Recommended extension"):
        encoder(
            dummy_pcm,
            PCMFormat.F32LE,
            PCMSampleRate.RATE_44K,
            PCMChannels.STEREO,
            tmp_path / "out.txt",
        )

    # 3. File already exists and overwrite=False
    out_file = tmp_path / "existing.mp3"
    out_file.write_bytes(b"dummy")
    with pytest.raises(ValueError, match="Output file already exists"):
        encoder(
            dummy_pcm,
            PCMFormat.F32LE,
            PCMSampleRate.RATE_44K,
            PCMChannels.STEREO,
            out_file,
            overwrite=False,
        )

    # 4. Decoder with non-existent file
    non_existent = tmp_path / "does_not_exist.mp3"
    with pytest.raises(FileNotFoundError, match="Audio file not found"):
        decode_to_PCM_F32LE_with_ffmpeg(non_existent)

    # 5. FFprobe with non-existent file
    with pytest.raises(FileNotFoundError, match="Audio file not found"):
        get_audio_info_from_ffprobe(non_existent)
