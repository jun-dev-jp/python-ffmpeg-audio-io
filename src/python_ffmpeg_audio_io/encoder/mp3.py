"""MP3 encoder module using FFmpeg."""

from __future__ import annotations

from enum import Enum
from os import PathLike

from ..pcm import PCM
from .base import BaseAudioEncoder

SUPPORTED_MP3_FORMAT_NAMES = ["mp3"]


class MP3EncoderBitrate(Enum):
    """Enum for MP3 encoder bitrate options."""

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


class MP3EncoderMode(Enum):
    """Enum for MP3 encoder mode options."""

    ABR = "ABR"
    CBR = "CBR"
    VBR = "VBR"


class MP3EncoderQualityLevel(Enum):
    """Enum for VBR quality levels (0-9, where 0 is best and 9 is worst)."""

    Quality_0 = 0
    Quality_1 = 1
    Quality_2 = 2
    Quality_3 = 3
    Quality_4 = 4
    Quality_5 = 5
    Quality_6 = 6
    Quality_7 = 7
    Quality_8 = 8
    Quality_9 = 9


class MP3Encoder(BaseAudioEncoder):
    """Encoder class for encoding PCM audio data to MP3 format using FFmpeg."""

    def __init__(
        self,
        bitrate: MP3EncoderBitrate = MP3EncoderBitrate.Kbps_192,
        mode: MP3EncoderMode = MP3EncoderMode.CBR,
        quality: MP3EncoderQualityLevel = MP3EncoderQualityLevel.Quality_2,
    ) -> None:
        if not isinstance(bitrate, MP3EncoderBitrate):
            t_name = type(bitrate).__name__
            raise TypeError(f"bitrate must be MP3EncoderBitrate, got {t_name}")
        if not isinstance(mode, MP3EncoderMode):
            t_name = type(mode).__name__
            raise TypeError(f"mode must be MP3EncoderMode, got {t_name}")
        if not isinstance(quality, MP3EncoderQualityLevel):
            t_name = type(quality).__name__
            raise TypeError(f"quality must be MP3EncoderQualityLevel, got {t_name}")

        self._codec: str = "libmp3lame"
        self._bitrate: MP3EncoderBitrate = bitrate
        self._quality: MP3EncoderQualityLevel = quality
        self._mode: MP3EncoderMode = mode

    def __call__(
        self,
        pcm: PCM,
        output_path: str | PathLike[str],
        overwrite: bool = False,
    ) -> None:
        """Encode PCM audio data to MP3 format and save to destination path.

        Args:
            pcm: PCM audio data to encode.
            output_path: Destination path for the encoded MP3 file.
            overwrite: Whether to overwrite existing output file.

        Raises:
            TypeError: If arguments are of incorrect type.
            ValueError: If output format extension is unsupported.
            FileWriteError: If output file exists and overwrite is False.
            FFmpegNotFoundError: If FFmpeg executable is not found in PATH.
            FFmpegError: If FFmpeg encoding fails.
        """
        dest_path = self._check_output_path(
            output_path, SUPPORTED_MP3_FORMAT_NAMES, overwrite
        )

        codec_args: list[str] = ["-c:a", self._codec]
        if self._mode == MP3EncoderMode.ABR:
            codec_args += ["-abr", "1", "-b:a", self._bitrate.value]
        elif self._mode == MP3EncoderMode.VBR:
            codec_args += ["-qscale:a", str(self._quality.value)]
        else:  # CBR
            codec_args += ["-b:a", self._bitrate.value]

        self._run_ffmpeg_encode(codec_args, pcm, dest_path, overwrite)

    @property
    def codec(self) -> str:
        """Return the codec name used for MP3 encoding."""
        return self._codec

    @property
    def bitrate(self) -> MP3EncoderBitrate:
        """Return the bitrate of the MP3 encoder."""
        return self._bitrate

    @bitrate.setter
    def bitrate(self, value: MP3EncoderBitrate) -> None:
        """Set the bitrate of the MP3 encoder."""
        if not isinstance(value, MP3EncoderBitrate):
            t_name = type(value).__name__
            raise TypeError(f"bitrate must be MP3EncoderBitrate, got {t_name}")
        self._bitrate = value

    @property
    def quality(self) -> MP3EncoderQualityLevel:
        """Return the quality level of the MP3 encoder."""
        return self._quality

    @quality.setter
    def quality(self, value: MP3EncoderQualityLevel) -> None:
        """Set the quality level of the MP3 encoder."""
        if not isinstance(value, MP3EncoderQualityLevel):
            t_name = type(value).__name__
            raise TypeError(f"quality must be MP3EncoderQualityLevel, got {t_name}")
        self._quality = value

    @property
    def mode(self) -> MP3EncoderMode:
        """Return the mode of the MP3 encoder."""
        return self._mode

    @mode.setter
    def mode(self, value: MP3EncoderMode) -> None:
        """Set the mode of the MP3 encoder."""
        if not isinstance(value, MP3EncoderMode):
            t_name = type(value).__name__
            raise TypeError(f"mode must be MP3EncoderMode, got {t_name}")
        self._mode = value
