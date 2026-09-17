"""AAC audio stream writer module using FFmpeg."""

from __future__ import annotations

from collections.abc import Sequence
from os import PathLike

from ..encoder.aac import (
    SUPPORTED_MP4_FORMAT_NAMES,
    AACEncoderBitrate,
    AACEncoderMode,
    AACEncoderQualityLevel,
)
from ..exceptions import AudioTypeError
from ..pcm import PCMChannels, PCMFormat, PCMSampleRate
from .base import BaseAudioStreamWriter


class AACStreamWriter(BaseAudioStreamWriter):
    """Stream writer for encoding PCM audio data to AAC format using FFmpeg.

    Attributes:
        codec: Audio codec name used by FFmpeg ("aac").
        bitrate: Bitrate configuration for AAC encoding.
        mode: Bitrate mode (CBR, VBR, ABR).
        quality: VBR quality level (0-5).
    """

    _codec: str
    _bitrate: AACEncoderBitrate
    _mode: AACEncoderMode
    _quality: AACEncoderQualityLevel

    def __init__(
        self,
        output_path: str | PathLike[str],
        sample_rate: PCMSampleRate | int = PCMSampleRate.RATE_44K,
        channels: PCMChannels | int = PCMChannels.STEREO,
        pcm_format: PCMFormat = PCMFormat.F32LE,
        overwrite: bool = False,
        bitrate: AACEncoderBitrate = AACEncoderBitrate.Kbps_192,
        mode: AACEncoderMode = AACEncoderMode.CBR,
        quality: AACEncoderQualityLevel = AACEncoderQualityLevel.Quality_5,
    ) -> None:
        """Initialize AACStreamWriter.

        Args:
            output_path: Destination path for the AAC/M4A/MP4 file.
            sample_rate: Sample rate of the incoming PCM stream (default: 44.1kHz).
            channels: Channel count of the incoming PCM stream (default: Stereo).
            pcm_format: PCM format of incoming audio (default: F32LE).
            overwrite: Whether to overwrite existing file (default: False).
            bitrate: Target bitrate (default: 192k).
            mode: Encoding mode: CBR, VBR, or ABR (default: CBR).
            quality: VBR quality level 0-5 (default: Quality_5).

        Raises:
            AudioTypeError: If arguments are of incorrect type.
            AudioValueError: If sample_rate, channels, or output file extension is
                unsupported.
            FileWriteError: If output file exists and overwrite is False.
            FFmpegNotFoundError: If FFmpeg executable is not in PATH.
            FFmpegError: If FFmpeg fails to start.
        """
        if not isinstance(bitrate, AACEncoderBitrate):
            t_name = type(bitrate).__name__
            raise AudioTypeError(f"bitrate must be AACEncoderBitrate, got {t_name}")
        if not isinstance(mode, AACEncoderMode):
            t_name = type(mode).__name__
            raise AudioTypeError(f"mode must be AACEncoderMode, got {t_name}")
        if not isinstance(quality, AACEncoderQualityLevel):
            t_name = type(quality).__name__
            raise AudioTypeError(
                f"quality must be AACEncoderQualityLevel, got {t_name}"
            )

        self._codec = "aac"
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
        """Return supported file extension names for AAC."""
        return SUPPORTED_MP4_FORMAT_NAMES

    def _get_codec_args(self) -> Sequence[str]:
        """Return AAC codec arguments for FFmpeg."""
        codec_args: list[str] = ["-c:a", self._codec]
        if self._mode == AACEncoderMode.ABR:
            codec_args += ["-abr", "1", "-b:a", self._bitrate.value]
        elif self._mode == AACEncoderMode.VBR:
            codec_args += ["-q:a", str(self._quality.value)]
        else:  # CBR
            codec_args += ["-b:a", self._bitrate.value]
        return codec_args

    @property
    def codec(self) -> str:
        """Return the codec name used for AAC encoding."""
        return self._codec

    @property
    def bitrate(self) -> AACEncoderBitrate:
        """Return the bitrate configuration."""
        return self._bitrate

    @property
    def mode(self) -> AACEncoderMode:
        """Return the encoder mode."""
        return self._mode

    @property
    def quality(self) -> AACEncoderQualityLevel:
        """Return the quality level."""
        return self._quality


__all__ = ["AACStreamWriter"]
