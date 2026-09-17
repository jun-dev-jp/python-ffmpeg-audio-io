"""AAC encoder module using FFmpeg."""

from __future__ import annotations

from enum import Enum
from os import PathLike

from ..exceptions import AudioTypeError
from ..pcm import PCM
from .base import BaseAudioEncoder

SUPPORTED_MP4_FORMAT_NAMES = ["mp4", "m4a", "aac"]


class AACEncoderBitrate(Enum):
    """Enum for AAC encoder bitrate options."""

    Kbps_64 = "64k"
    Kbps_96 = "96k"
    Kbps_128 = "128k"
    Kbps_160 = "160k"
    Kbps_192 = "192k"
    Kbps_224 = "224k"
    Kbps_256 = "256k"
    Kbps_288 = "288k"
    Kbps_320 = "320k"
    Kbps_352 = "352k"
    Kbps_384 = "384k"


class AACEncoderMode(Enum):
    """Enum for AAC encoder mode options."""

    ABR = "ABR"
    CBR = "CBR"
    VBR = "VBR"


class AACEncoderQualityLevel(Enum):
    """Enum for VBR quality levels (0-5, where 5 is best and 0 is worst)."""

    Quality_0 = 0
    Quality_1 = 1
    Quality_2 = 2
    Quality_3 = 3
    Quality_4 = 4
    Quality_5 = 5


class AACEncoder(BaseAudioEncoder):
    """Encoder class for encoding PCM audio data to AAC format using FFmpeg."""

    def __init__(
        self,
        bitrate: AACEncoderBitrate = AACEncoderBitrate.Kbps_192,
        mode: AACEncoderMode = AACEncoderMode.CBR,
        quality: AACEncoderQualityLevel = AACEncoderQualityLevel.Quality_5,
    ) -> None:
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

        self._codec: str = "aac"
        self._bitrate: AACEncoderBitrate = bitrate
        self._quality: AACEncoderQualityLevel = quality
        self._mode: AACEncoderMode = mode

    def __call__(
        self,
        pcm: PCM,
        output_path: str | PathLike[str],
        overwrite: bool = False,
    ) -> None:
        """Encode PCM audio data to AAC format and save to destination path.

        Args:
            pcm: PCM audio data to encode.
            output_path: Destination path for the encoded AAC file.
            overwrite: Whether to overwrite existing output file.

        Raises:
            AudioTypeError: If arguments are of incorrect type.
            AudioValueError: If output format extension is unsupported.
            FileWriteError: If output file exists and overwrite is False.
            FFmpegNotFoundError: If FFmpeg executable is not found in PATH.
            FFmpegError: If FFmpeg encoding fails.
        """
        dest_path = self._check_output_path(
            output_path, SUPPORTED_MP4_FORMAT_NAMES, overwrite
        )

        codec_args: list[str] = ["-c:a", self._codec]
        if self._mode == AACEncoderMode.ABR:
            codec_args += ["-abr", "1", "-b:a", self._bitrate.value]
        elif self._mode == AACEncoderMode.VBR:
            codec_args += ["-q:a", str(self._quality.value)]
        else:  # CBR
            codec_args += ["-b:a", self._bitrate.value]

        self._run_ffmpeg_encode(codec_args, pcm, dest_path, overwrite)

    @property
    def codec(self) -> str:
        """Return the codec name used for AAC encoding."""
        return self._codec

    @property
    def bitrate(self) -> AACEncoderBitrate:
        """Return the bitrate of the AAC encoder."""
        return self._bitrate

    @bitrate.setter
    def bitrate(self, value: AACEncoderBitrate) -> None:
        """Set the bitrate of the AAC encoder."""
        if not isinstance(value, AACEncoderBitrate):
            t_name = type(value).__name__
            raise AudioTypeError(f"bitrate must be AACEncoderBitrate, got {t_name}")
        self._bitrate = value

    @property
    def quality(self) -> AACEncoderQualityLevel:
        """Return the quality level of the AAC encoder."""
        return self._quality

    @quality.setter
    def quality(self, value: AACEncoderQualityLevel) -> None:
        """Set the quality level of the AAC encoder."""
        if not isinstance(value, AACEncoderQualityLevel):
            t_name = type(value).__name__
            raise AudioTypeError(
                f"quality must be AACEncoderQualityLevel, got {t_name}"
            )
        self._quality = value

    @property
    def mode(self) -> AACEncoderMode:
        """Return the mode of the AAC encoder."""
        return self._mode

    @mode.setter
    def mode(self, value: AACEncoderMode) -> None:
        """Set the mode of the AAC encoder."""
        if not isinstance(value, AACEncoderMode):
            t_name = type(value).__name__
            raise AudioTypeError(f"mode must be AACEncoderMode, got {t_name}")
        self._mode = value


__all__ = [
    "SUPPORTED_MP4_FORMAT_NAMES",
    "AACEncoder",
    "AACEncoderBitrate",
    "AACEncoderMode",
    "AACEncoderQualityLevel",
]
