"""FLAC encoder module using FFmpeg."""

from __future__ import annotations

from enum import Enum
from os import PathLike

from ..exceptions import AudioTypeError
from ..pcm import PCM
from .base import BaseAudioEncoder

SUPPORTED_FLAC_FORMAT_NAMES = ["flac"]


class FLACEncoderCompressionLevel(Enum):
    """Enum for FLAC compression levels (0-12: 0=fastest, 12=highest)."""

    Level_0 = 0
    Level_1 = 1
    Level_2 = 2
    Level_3 = 3
    Level_4 = 4
    Level_5 = 5
    Level_6 = 6
    Level_7 = 7
    Level_8 = 8
    Level_9 = 9
    Level_10 = 10
    Level_11 = 11
    Level_12 = 12


class FLACEncoder(BaseAudioEncoder):
    """Encoder class for encoding PCM audio data to FLAC format using FFmpeg."""

    def __init__(
        self,
        compression_level: FLACEncoderCompressionLevel = (
            FLACEncoderCompressionLevel.Level_5
        ),
    ) -> None:
        if not isinstance(compression_level, FLACEncoderCompressionLevel):
            t_name = type(compression_level).__name__
            raise AudioTypeError(
                f"compression_level must be FLACEncoderCompressionLevel, got {t_name}"
            )

        self._codec: str = "flac"
        self._compression_level: FLACEncoderCompressionLevel = compression_level

    def __call__(
        self,
        pcm: PCM,
        output_path: str | PathLike[str],
        overwrite: bool = False,
    ) -> None:
        """Encode PCM audio data to FLAC format and save to destination path.

        Args:
            pcm: PCM audio data to encode.
            output_path: Destination path for the encoded FLAC file.
            overwrite: Whether to overwrite existing output file.

        Raises:
            AudioTypeError: If arguments are of incorrect type.
            AudioValueError: If output format extension is unsupported.
            FileWriteError: If output file exists and overwrite is False.
            FFmpegNotFoundError: If FFmpeg executable is not found in PATH.
            FFmpegError: If FFmpeg encoding fails.
        """
        dest_path = self._check_output_path(
            output_path, SUPPORTED_FLAC_FORMAT_NAMES, overwrite
        )

        codec_args: list[str] = [
            "-c:a",
            self._codec,
            "-compression_level",
            str(self._compression_level.value),
        ]

        self._run_ffmpeg_encode(codec_args, pcm, dest_path, overwrite)

    @property
    def codec(self) -> str:
        """Return the codec name used for FLAC encoding."""
        return self._codec

    @property
    def compression_level(self) -> FLACEncoderCompressionLevel:
        """Return the compression level of the FLAC encoder."""
        return self._compression_level

    @compression_level.setter
    def compression_level(self, value: FLACEncoderCompressionLevel) -> None:
        """Set the compression level of the FLAC encoder."""
        if not isinstance(value, FLACEncoderCompressionLevel):
            t_name = type(value).__name__
            raise AudioTypeError(
                f"compression_level must be FLACEncoderCompressionLevel, got {t_name}"
            )
        self._compression_level = value


__all__ = [
    "SUPPORTED_FLAC_FORMAT_NAMES",
    "FLACEncoder",
    "FLACEncoderCompressionLevel",
]
