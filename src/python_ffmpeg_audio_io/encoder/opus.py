"""Opus encoder module using FFmpeg."""

from __future__ import annotations

from enum import Enum
from os import PathLike

from ..exceptions import AudioTypeError
from ..pcm import PCM
from .base import BaseAudioEncoder

SUPPORTED_OPUS_FORMAT_NAMES = ["opus", "ogg"]


class OpusEncoderBitrate(Enum):
    """Enum for Opus encoder bitrate options."""

    Kbps_32 = "32k"
    Kbps_48 = "48k"
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
    Kbps_448 = "448k"
    Kbps_510 = "510k"


class OpusEncoderMode(Enum):
    """Enum for Opus encoder mode options."""

    VBR = "VBR"
    CBR = "CBR"
    CVBR = "CVBR"


class OpusEncoderApplication(Enum):
    """Enum for Opus encoder application type options."""

    AUDIO = "audio"
    VOIP = "voip"
    LOW_DELAY = "lowdelay"


class OpusEncoder(BaseAudioEncoder):
    """Encoder class for encoding PCM audio data to Opus format using FFmpeg."""

    def __init__(
        self,
        bitrate: OpusEncoderBitrate = OpusEncoderBitrate.Kbps_128,
        mode: OpusEncoderMode = OpusEncoderMode.VBR,
        application: OpusEncoderApplication = OpusEncoderApplication.AUDIO,
    ) -> None:
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

        self._codec: str = "libopus"
        self._bitrate: OpusEncoderBitrate = bitrate
        self._mode: OpusEncoderMode = mode
        self._application: OpusEncoderApplication = application

    def __call__(
        self,
        pcm: PCM,
        output_path: str | PathLike[str],
        overwrite: bool = False,
    ) -> None:
        """Encode PCM audio data to Opus format and save to destination path.

        Args:
            pcm: PCM audio data to encode.
            output_path: Destination path for the encoded Opus file.
            overwrite: Whether to overwrite existing output file.

        Raises:
            AudioTypeError: If arguments are of incorrect type.
            AudioValueError: If output format extension is unsupported.
            FileWriteError: If output file exists and overwrite is False.
            FFmpegNotFoundError: If FFmpeg executable is not found in PATH.
            FFmpegError: If FFmpeg encoding fails.
        """
        dest_path = self._check_output_path(
            output_path, SUPPORTED_OPUS_FORMAT_NAMES, overwrite
        )

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

        self._run_ffmpeg_encode(codec_args, pcm, dest_path, overwrite)

    @property
    def codec(self) -> str:
        """Return the codec name used for Opus encoding."""
        return self._codec

    @property
    def bitrate(self) -> OpusEncoderBitrate:
        """Return the bitrate of the Opus encoder."""
        return self._bitrate

    @bitrate.setter
    def bitrate(self, value: OpusEncoderBitrate) -> None:
        """Set the bitrate of the Opus encoder."""
        if not isinstance(value, OpusEncoderBitrate):
            t_name = type(value).__name__
            raise AudioTypeError(f"bitrate must be OpusEncoderBitrate, got {t_name}")
        self._bitrate = value

    @property
    def mode(self) -> OpusEncoderMode:
        """Return the mode of the Opus encoder."""
        return self._mode

    @mode.setter
    def mode(self, value: OpusEncoderMode) -> None:
        """Set the mode of the Opus encoder."""
        if not isinstance(value, OpusEncoderMode):
            t_name = type(value).__name__
            raise AudioTypeError(f"mode must be OpusEncoderMode, got {t_name}")
        self._mode = value

    @property
    def application(self) -> OpusEncoderApplication:
        """Return the application type of the Opus encoder."""
        return self._application

    @application.setter
    def application(self, value: OpusEncoderApplication) -> None:
        """Set the application type of the Opus encoder."""
        if not isinstance(value, OpusEncoderApplication):
            t_name = type(value).__name__
            raise AudioTypeError(
                f"application must be OpusEncoderApplication, got {t_name}"
            )
        self._application = value


__all__ = [
    "SUPPORTED_OPUS_FORMAT_NAMES",
    "OpusEncoder",
    "OpusEncoderApplication",
    "OpusEncoderBitrate",
    "OpusEncoderMode",
]
