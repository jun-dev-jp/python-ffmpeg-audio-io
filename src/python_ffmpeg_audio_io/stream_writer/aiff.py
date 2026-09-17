"""AIFF audio stream writer module using FFmpeg."""

from __future__ import annotations

from collections.abc import Sequence
from os import PathLike

from ..encoder.aiff import SUPPORTED_AIFF_FORMAT_NAMES
from ..exceptions import AudioTypeError
from ..pcm import PCMChannels, PCMCodec, PCMFormat, PCMSampleRate
from .base import BaseAudioStreamWriter


class AIFFStreamWriter(BaseAudioStreamWriter):
    """Stream writer for encoding PCM audio data to AIFF format using FFmpeg.

    Attributes:
        codec: PCMCodec used for the AIFF container.
    """

    _codec: PCMCodec

    def __init__(
        self,
        output_path: str | PathLike[str],
        sample_rate: PCMSampleRate | int = PCMSampleRate.RATE_44K,
        channels: PCMChannels | int = PCMChannels.STEREO,
        pcm_format: PCMFormat = PCMFormat.F32LE,
        overwrite: bool = False,
        codec: PCMCodec = PCMCodec.PCM_S16BE,
    ) -> None:
        """Initialize AIFFStreamWriter.

        Args:
            output_path: Destination path for the AIFF file.
            sample_rate: Sample rate of the incoming PCM stream (default: 44.1kHz).
            channels: Channel count of the incoming PCM stream (default: Stereo).
            pcm_format: PCM format of incoming audio (default: F32LE).
            overwrite: Whether to overwrite existing file (default: False).
            codec: Audio PCMCodec for AIFF encoding (default: PCM_S16BE).

        Raises:
            AudioTypeError: If arguments are of incorrect type.
            AudioValueError: If sample_rate, channels, or output file extension is
                unsupported.
            FileWriteError: If output file exists and overwrite is False.
            FFmpegNotFoundError: If FFmpeg executable is not in PATH.
            FFmpegError: If FFmpeg fails to start.
        """
        if not isinstance(codec, PCMCodec):
            t_name = type(codec).__name__
            raise AudioTypeError(f"codec must be an instance of PCMCodec, got {t_name}")

        self._codec = codec

        super().__init__(
            output_path=output_path,
            sample_rate=sample_rate,
            channels=channels,
            pcm_format=pcm_format,
            overwrite=overwrite,
        )

    @property
    def supported_formats(self) -> Sequence[str]:
        """Return supported file extension names for AIFF."""
        return SUPPORTED_AIFF_FORMAT_NAMES

    def _get_codec_args(self) -> Sequence[str]:
        """Return AIFF codec arguments for FFmpeg."""
        return [
            "-c:a",
            self._codec.value,
            "-f",
            "aiff",
        ]

    @property
    def codec(self) -> PCMCodec:
        """Return the PCM codec used for AIFF encoding."""
        return self._codec


__all__ = ["AIFFStreamWriter"]
