"""MP3 audio stream writer module using FFmpeg."""

from __future__ import annotations

from collections.abc import Sequence
from os import PathLike

from ..encoder.mp3 import (
    SUPPORTED_MP3_FORMAT_NAMES,
    MP3EncoderBitrate,
    MP3EncoderMode,
    MP3EncoderQualityLevel,
)
from ..pcm import PCMChannels, PCMFormat, PCMSampleRate
from .base import BaseAudioStreamWriter


class MP3StreamWriter(BaseAudioStreamWriter):
    """Stream writer for encoding PCM audio data to MP3 format using FFmpeg.

    Attributes:
        codec: Audio codec name used by FFmpeg ("libmp3lame").
        bitrate: Bitrate configuration for MP3 encoding.
        mode: Bitrate mode (CBR, VBR, ABR).
        quality: VBR quality level (0-9).
    """

    _codec: str
    _bitrate: MP3EncoderBitrate
    _mode: MP3EncoderMode
    _quality: MP3EncoderQualityLevel

    def __init__(
        self,
        output_path: str | PathLike[str],
        sample_rate: PCMSampleRate | int = PCMSampleRate.RATE_44K,
        channels: PCMChannels | int = PCMChannels.STEREO,
        pcm_format: PCMFormat = PCMFormat.F32LE,
        overwrite: bool = False,
        bitrate: MP3EncoderBitrate = MP3EncoderBitrate.Kbps_192,
        mode: MP3EncoderMode = MP3EncoderMode.CBR,
        quality: MP3EncoderQualityLevel = MP3EncoderQualityLevel.Quality_2,
    ) -> None:
        """Initialize MP3StreamWriter.

        Args:
            output_path: Destination path for the MP3 file.
            sample_rate: Sample rate of the incoming PCM stream (default: 44.1kHz).
            channels: Channel count of the incoming PCM stream (default: Stereo).
            pcm_format: PCM format of incoming audio (default: F32LE).
            overwrite: Whether to overwrite existing file (default: False).
            bitrate: Target bitrate (default: 192k).
            mode: Encoding mode: CBR, VBR, or ABR (default: CBR).
            quality: VBR quality level 0-9 (default: Quality_2).

        Raises:
            TypeError: If arguments are of incorrect type.
            ValueError: If sample_rate, channels, or output file extension is
                unsupported.
            FileWriteError: If output file exists and overwrite is False.
            FFmpegNotFoundError: If FFmpeg executable is not in PATH.
            FFmpegError: If FFmpeg fails to start.
        """
        if not isinstance(bitrate, MP3EncoderBitrate):
            t_name = type(bitrate).__name__
            raise TypeError(f"bitrate must be MP3EncoderBitrate, got {t_name}")
        if not isinstance(mode, MP3EncoderMode):
            t_name = type(mode).__name__
            raise TypeError(f"mode must be MP3EncoderMode, got {t_name}")
        if not isinstance(quality, MP3EncoderQualityLevel):
            t_name = type(quality).__name__
            raise TypeError(f"quality must be MP3EncoderQualityLevel, got {t_name}")

        self._codec = "libmp3lame"
        self._bitrate = bitrate
        self._mode = mode
        self._quality = quality

        super().__init__(
            output_path=output_path,
            sample_rate=sample_rate,
            channels=channels,
            pcm_format=pcm_format,
            overwrite=overwrite,
        )

    @property
    def supported_formats(self) -> Sequence[str]:
        """Return supported file extension names for MP3."""
        return SUPPORTED_MP3_FORMAT_NAMES

    def _get_codec_args(self) -> Sequence[str]:
        """Return MP3 codec arguments for FFmpeg."""
        codec_args: list[str] = ["-c:a", self._codec]
        if self._mode == MP3EncoderMode.ABR:
            codec_args += ["-abr", "1", "-b:a", self._bitrate.value]
        elif self._mode == MP3EncoderMode.VBR:
            codec_args += ["-qscale:a", str(self._quality.value)]
        else:  # CBR
            codec_args += ["-b:a", self._bitrate.value]
        return codec_args

    @property
    def codec(self) -> str:
        """Return the codec name used for MP3 encoding."""
        return self._codec

    @property
    def bitrate(self) -> MP3EncoderBitrate:
        """Return the bitrate configuration."""
        return self._bitrate

    @property
    def mode(self) -> MP3EncoderMode:
        """Return the encoder mode."""
        return self._mode

    @property
    def quality(self) -> MP3EncoderQualityLevel:
        """Return the quality level."""
        return self._quality


__all__ = ["MP3StreamWriter"]
