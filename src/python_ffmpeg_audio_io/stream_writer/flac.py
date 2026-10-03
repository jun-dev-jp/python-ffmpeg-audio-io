"""FLAC audio stream writer module using FFmpeg."""

from __future__ import annotations

from collections.abc import Sequence
from os import PathLike

from ..encoder.flac import (
    SUPPORTED_FLAC_FORMAT_NAMES,
    FLACEncoderCompressionLevel,
)
from ..exceptions import AudioTypeError
from ..pcm import PCMChannels, PCMFormat, PCMSampleRate
from .base import BaseAudioStreamWriter


class FLACStreamWriter(BaseAudioStreamWriter):
    """Stream writer for encoding PCM audio data to FLAC format using FFmpeg.

    Attributes:
        codec: Audio codec name used by FFmpeg ("flac").
        compression_level: FLAC compression level (Level_0 to Level_12).
    """

    _codec: str
    _compression_level: FLACEncoderCompressionLevel

    def __init__(
        self,
        output_path: str | PathLike[str],
        sample_rate: PCMSampleRate = PCMSampleRate.RATE_44K,
        channels: PCMChannels = PCMChannels.STEREO,
        pcm_format: PCMFormat = PCMFormat.F32LE,
        overwrite: bool = False,
        compression_level: FLACEncoderCompressionLevel = (
            FLACEncoderCompressionLevel.Level_5
        ),
    ) -> None:
        """Initialize FLACStreamWriter.

        Args:
            output_path: Destination path for the FLAC file.
            sample_rate: Sample rate of the incoming PCM stream (default: 44.1kHz).
            channels: Channel count of the incoming PCM stream (default: Stereo).
            pcm_format: PCM format of incoming audio (default: F32LE).
            overwrite: Whether to overwrite existing file (default: False).
            compression_level: Compression level 0-12 (default: Level_5).

        Raises:
            AudioTypeError: If arguments are of incorrect type.
            AudioValueError: If sample_rate, channels, or output file extension is
                unsupported.
            FileWriteError: If output file exists and overwrite is False.
            FFmpegNotFoundError: If FFmpeg executable is not in PATH.
            FFmpegError: If FFmpeg fails to start.
        """
        if not isinstance(compression_level, FLACEncoderCompressionLevel):
            t_name = type(compression_level).__name__
            raise AudioTypeError(
                f"compression_level must be FLACEncoderCompressionLevel, got {t_name}"
            )

        self._codec = "flac"
        self._compression_level = compression_level

        super().__init__(
            output_path=output_path,
            sample_rate=sample_rate,
            channels=channels,
            pcm_format=pcm_format,
            overwrite=overwrite,
        )

    @property
    def supported_formats(self) -> Sequence[str]:
        """Return supported file extension names for FLAC."""
        return SUPPORTED_FLAC_FORMAT_NAMES

    def _get_codec_args(self) -> Sequence[str]:
        """Return FLAC codec arguments for FFmpeg."""
        return [
            "-c:a",
            self._codec,
            "-compression_level",
            str(self._compression_level.value),
        ]

    @property
    def codec(self) -> str:
        """Return the codec name used for FLAC encoding."""
        return self._codec

    @property
    def compression_level(self) -> FLACEncoderCompressionLevel:
        """Return the compression level configuration."""
        return self._compression_level


__all__ = ["FLACStreamWriter"]
