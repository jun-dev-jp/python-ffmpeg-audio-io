from __future__ import annotations

import logging
import subprocess
from pathlib import Path

from ..exceptions import FFmpegError, FFmpegNotFoundError
from ..pcm import PCMChannels, PCMCodec, PCMFormat, PCMSampleRate

SUPPORTED_AIFF_FORMAT_NAMES = ["aiff", "aif"]

logger = logging.getLogger(__name__)

PathLike = str | Path


class AIFFEncoder:
    """Encoder class for encoding PCM audio data to AIFF format using FFmpeg."""

    def __init__(
        self,
        codec: PCMCodec = PCMCodec.PCM_S16BE,
    ) -> None:
        self._codec: PCMCodec = codec

    def __call__(
        self,
        pcm_data: bytes,
        pcm_format: PCMFormat,
        sample_rate: PCMSampleRate,
        channels: PCMChannels,
        output_path: PathLike,
        overwrite: bool = False,
    ) -> bool:
        """Encodes PCM audio data to AIFF format and saves it to the specified output path.

        Args:
            pcm_data: Raw PCM audio bytes.
            pcm_format: PCM sample format (e.g. PCMFormat.S16BE).
            sample_rate: Audio sample rate.
            channels: Number of audio channels.
            output_path: Destination path for the encoded AIFF file.
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
            for fmt in SUPPORTED_AIFF_FORMAT_NAMES
        ):
            raise ValueError(
                f"Recommended extension for output file is one of {['.' + fmt for fmt in SUPPORTED_AIFF_FORMAT_NAMES]} for AIFF format."
            )
        if out_path.exists() and not overwrite:
            raise ValueError(
                f"Output file already exists and overwrite is disabled: {out_path}"
            )

        return self._encode_to_aiff_with_ffmpeg(
            pcm_data, pcm_format, sample_rate, channels, out_path, overwrite
        )

    def _encode_to_aiff_with_ffmpeg(
        self,
        pcm_data: bytes,
        pcm_format: PCMFormat,
        sample_rate: PCMSampleRate,
        channels: PCMChannels,
        output_path: Path,
        overwrite: bool,
    ) -> bool:
        """Internal method to encode PCM data to AIFF format using ffmpeg."""
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
        cmd += ["-c:a", self._codec.value]
        cmd += ["-f", "aiff"]
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
                f"FFmpeg failed to encode AIFF to {output_path}: {err_msg}",
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
    def codec(self) -> PCMCodec:
        """Returns the codec used for AIFF encoding."""
        return self._codec

    @codec.setter
    def codec(self, value: PCMCodec) -> None:
        """Sets the codec of the AIFF encoder."""
        if not isinstance(value, PCMCodec):
            raise TypeError(
                f"Invalid codec value: {value}. Expected a PCMCodec enum member."
            )
        self._codec = value
