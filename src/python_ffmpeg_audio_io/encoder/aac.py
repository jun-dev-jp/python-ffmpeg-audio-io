"""AAC encoder module using ffmpeg."""

from __future__ import annotations

import logging
import subprocess
from enum import Enum
from pathlib import Path

from ..exceptions import FFmpegError, FFmpegNotFoundError
from ..pcm import PCMChannels, PCMFormat, PCMSampleRate

SUPPORTED_MP4_FORMAT_NAMES = ["mp4", "m4a", "aac"]

logger = logging.getLogger(__name__)

PathLike = str | Path


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


class AACEncoder:
    """Encoder class for encoding PCM audio data to AAC format using FFmpeg."""

    def __init__(
        self,
        bitrate: AACEncoderBitrate = AACEncoderBitrate.Kbps_192,
        mode: AACEncoderMode = AACEncoderMode.CBR,
        quality: AACEncoderQualityLevel = AACEncoderQualityLevel.Quality_5,
    ) -> None:
        self._codec: str = "aac"
        self._bitrate: AACEncoderBitrate = bitrate
        self._quality: AACEncoderQualityLevel = quality
        self._mode: AACEncoderMode = mode

    def __call__(
        self,
        pcm_data: bytes,
        pcm_format: PCMFormat,
        sample_rate: PCMSampleRate,
        channels: PCMChannels,
        output_path: PathLike,
        overwrite: bool = False,
    ) -> bool:
        """Encodes PCM audio data to AAC format and saves it to the specified output path.

        Args:
            pcm_data: Raw PCM audio bytes.
            pcm_format: PCM sample format (e.g. PCMFormat.F32LE).
            sample_rate: Audio sample rate.
            channels: Number of audio channels.
            output_path: Destination path for the encoded AAC file.
            overwrite: Whether to overwrite existing output file.

        Returns:
            bool: True on successful encoding.

        Raises:
            TypeError: If arguments are of incorrect type.
            ValueError: If output format is unsupported or file exists and overwrite is False.
            FFmpegError: If ffmpeg fails to encode.
        """
        if not isinstance(pcm_data, bytes):
            raise TypeError(f"Invalid PCM data type: {type(pcm_data)}. Expected bytes.")
        if not isinstance(pcm_format, PCMFormat):
            raise TypeError(f"Invalid PCM format: {pcm_format}. Expected PCMFormat.")
        if not isinstance(sample_rate, PCMSampleRate):
            raise TypeError(
                f"Invalid sample rate: {sample_rate}. Expected PCMSampleRate."
            )
        if not isinstance(channels, PCMChannels):
            raise TypeError(
                f"Invalid channels value: {channels}. Expected PCMChannels."
            )
        if not isinstance(output_path, (str, Path)):
            raise TypeError(
                f"Invalid output path provided: {type(output_path)}. Expected str or Path."
            )

        out_path = Path(output_path)
        if not any(
            out_path.name.lower().endswith("." + fmt)
            for fmt in SUPPORTED_MP4_FORMAT_NAMES
        ):
            raise ValueError(
                f"Recommended extension for output file is one of {['.' + fmt for fmt in SUPPORTED_MP4_FORMAT_NAMES]} for AAC format."
            )
        if out_path.exists() and not overwrite:
            raise ValueError(
                f"Output file already exists and overwrite is disabled: {out_path}"
            )

        return self._encode_to_aac_with_ffmpeg(
            pcm_data, pcm_format, sample_rate, channels, out_path, overwrite
        )

    def _encode_to_aac_with_ffmpeg(
        self,
        pcm_data: bytes,
        pcm_format: PCMFormat,
        sample_rate: PCMSampleRate,
        channels: PCMChannels,
        output_path: Path,
        overwrite: bool,
    ) -> bool:
        """Internal method to encode PCM data to AAC format using ffmpeg."""
        cmd = ["ffmpeg"]
        cmd += ["-y"] if overwrite else ["-n"]
        cmd += [
            "-f",
            pcm_format.value,
            "-ar",
            str(sample_rate.value),
            "-ac",
            str(channels.value),
            "-i",
            "pipe:0",
        ]
        cmd += ["-c:a", self._codec]
        if self._mode == AACEncoderMode.ABR:
            cmd += ["-abr", "1", "-b:a", self._bitrate.value]
        elif self._mode == AACEncoderMode.VBR:
            cmd += ["-q:a", str(self._quality.value)]
        else:  # CBR
            cmd += ["-b:a", self._bitrate.value]
        cmd += ["-loglevel", "error"]
        cmd += [str(output_path)]

        try:
            subprocess.run(
                cmd,
                input=pcm_data,
                capture_output=True,
                check=True,
            )
            return True
        except subprocess.CalledProcessError as e:
            err_msg = (
                e.stderr.decode("utf-8", errors="ignore").strip()
                if e.stderr
                else str(e)
            )
            logger.error(f"FFmpeg encoding failed: {err_msg}")
            raise FFmpegError(
                f"FFmpeg failed to encode AAC to {output_path}: {err_msg}",
                stderr=err_msg,
            ) from e
        except FileNotFoundError as e:
            logger.error("FFmpeg not found. Please install FFmpeg.")
            raise FFmpegNotFoundError(
                "FFmpeg executable not found. Please install FFmpeg."
            ) from e
        except OSError as e:
            if e.errno == 2:
                raise FFmpegNotFoundError(
                    "ffmpeg executable not found. Please ensure FFmpeg is installed and available in your PATH."
                ) from e
            logger.error(f"Failed to start ffmpeg process: {e}")
            raise FFmpegError(f"Failed to start ffmpeg process: {e}") from e

    @property
    def codec(self) -> str:
        """Returns the codec used for AAC encoding."""
        return self._codec

    @property
    def bitrate(self) -> AACEncoderBitrate:
        """Returns the bitrate of the AAC encoder."""
        return self._bitrate

    @bitrate.setter
    def bitrate(self, value: AACEncoderBitrate) -> None:
        """Sets the bitrate of the AAC encoder."""
        if not isinstance(value, AACEncoderBitrate):
            raise TypeError(
                f"Invalid bitrate value: {value}. Expected an AACEncoderBitrate enum member."
            )
        self._bitrate = value

    @property
    def quality(self) -> AACEncoderQualityLevel:
        """Returns the quality level of the AAC encoder."""
        return self._quality

    @quality.setter
    def quality(self, value: AACEncoderQualityLevel) -> None:
        """Sets the quality level of the AAC encoder."""
        if not isinstance(value, AACEncoderQualityLevel):
            raise TypeError(
                f"Invalid quality value: {value}. Expected an AACEncoderQualityLevel enum member."
            )
        self._quality = value

    @property
    def mode(self) -> AACEncoderMode:
        """Returns the mode of the AAC encoder."""
        return self._mode

    @mode.setter
    def mode(self, value: AACEncoderMode) -> None:
        """Sets the mode of the AAC encoder."""
        if not isinstance(value, AACEncoderMode):
            raise TypeError(
                f"Invalid mode value: {value}. Expected an AACEncoderMode enum member."
            )
        self._mode = value
