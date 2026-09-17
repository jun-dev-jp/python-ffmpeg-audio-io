"""Opus audio stream writer module using FFmpeg."""

from __future__ import annotations

from collections.abc import Sequence
from os import PathLike

from ..encoder.opus import (
    SUPPORTED_OPUS_FORMAT_NAMES,
    OpusEncoderApplication,
    OpusEncoderBitrate,
    OpusEncoderMode,
)
from ..exceptions import AudioTypeError
from ..pcm import PCMChannels, PCMFormat, PCMSampleRate
from .base import BaseAudioStreamWriter


class OpusStreamWriter(BaseAudioStreamWriter):
    """Stream writer for encoding PCM audio data to Opus format using FFmpeg.

    Attributes:
        codec: Audio codec name used by FFmpeg ("libopus").
        bitrate: Bitrate configuration for Opus encoding.
        mode: Bitrate mode (VBR, CBR, CVBR).
        application: Intended application type (audio, voip, lowdelay).
    """

    _codec: str
    _bitrate: OpusEncoderBitrate
    _mode: OpusEncoderMode
    _application: OpusEncoderApplication

    def __init__(
        self,
        output_path: str | PathLike[str],
        sample_rate: PCMSampleRate | int = PCMSampleRate.RATE_48K,
        channels: PCMChannels | int = PCMChannels.STEREO,
        pcm_format: PCMFormat = PCMFormat.F32LE,
        overwrite: bool = False,
        bitrate: OpusEncoderBitrate = OpusEncoderBitrate.Kbps_128,
        mode: OpusEncoderMode = OpusEncoderMode.VBR,
        application: OpusEncoderApplication = OpusEncoderApplication.AUDIO,
    ) -> None:
        """Initialize OpusStreamWriter.

        Args:
            output_path: Destination path for the Opus/OGG file.
            sample_rate: Sample rate of the incoming PCM stream (default: 48kHz).
            channels: Channel count of the incoming PCM stream (default: Stereo).
            pcm_format: PCM format of incoming audio (default: F32LE).
            overwrite: Whether to overwrite existing file (default: False).
            bitrate: Target bitrate (default: 128k).
            mode: Encoding mode: VBR, CBR, or CVBR (default: VBR).
            application: Intended application type (default: AUDIO).

        Raises:
            AudioTypeError: If arguments are of incorrect type.
            AudioValueError: If sample_rate, channels, or output file extension is
                unsupported.
            FileWriteError: If output file exists and overwrite is False.
            FFmpegNotFoundError: If FFmpeg executable is not in PATH.
            FFmpegError: If FFmpeg fails to start.
        """
        if not isinstance(bitrate, OpusEncoderBitrate):
            t_name = type(bitrate).__name__
            raise AudioTypeError(f"bitrate must be OpusEncoderBitrate, got {t_name}")
        if not isinstance(mode, OpusEncoderMode):
            t_name = type(mode).__name__
            raise AudioTypeError(f"mode must be OpusEncoderMode, got {t_name}")
        if not isinstance(application, OpusEncoderApplication):
            t_name = type(application).__name__
            raise AudioTypeError(
                f"application must be OpusEncoderApplication, got {t_name}"
            )

        self._codec = "libopus"
        self._bitrate = bitrate
        self._mode = mode
        self._application = application

        super().__init__(
            output_path=output_path,
            sample_rate=sample_rate,
            channels=channels,
            pcm_format=pcm_format,
            overwrite=overwrite,
        )

    @property
    def supported_formats(self) -> Sequence[str]:
        """Return supported file extension names for Opus."""
        return SUPPORTED_OPUS_FORMAT_NAMES

    def _get_codec_args(self) -> Sequence[str]:
        """Return Opus codec arguments for FFmpeg."""
        codec_args: list[str] = [
            "-c:a",
            self._codec,
            "-b:a",
            self._bitrate.value,
        ]

        if self._mode == OpusEncoderMode.CBR:
            codec_args += ["-vbr", "off"]
        elif self._mode == OpusEncoderMode.CVBR:
            codec_args += ["-vbr", "constrained"]
        else:  # VBR
            codec_args += ["-vbr", "on"]

        codec_args += ["-application", self._application.value]
        return codec_args

    @property
    def codec(self) -> str:
        """Return the codec name used for Opus encoding."""
        return self._codec

    @property
    def bitrate(self) -> OpusEncoderBitrate:
        """Return the bitrate configuration."""
        return self._bitrate

    @property
    def mode(self) -> OpusEncoderMode:
        """Return the encoder mode."""
        return self._mode

    @property
    def application(self) -> OpusEncoderApplication:
        """Return the application type configuration."""
        return self._application


__all__ = ["OpusStreamWriter"]
