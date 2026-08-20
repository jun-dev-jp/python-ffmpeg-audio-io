"""Base encoder module for audio encoders using FFmpeg."""

from __future__ import annotations

import logging
import subprocess
from abc import ABC, abstractmethod
from collections.abc import Sequence
from os import W_OK, PathLike, access
from pathlib import Path

from ..exceptions import FFmpegError, FFmpegNotFoundError, FileWriteError
from ..pcm import PCM

logger = logging.getLogger(__name__)


class BaseAudioEncoder(ABC):
    """Abstract base class for audio encoders powered by FFmpeg."""

    @abstractmethod
    def __call__(
        self,
        pcm: PCM,
        output_path: str | PathLike[str],
        overwrite: bool = False,
    ) -> None:
        """Encode PCM audio data to target format and save to destination path.

        Args:
            pcm: PCM audio data to encode.
            output_path: Destination path for the encoded audio file.
            overwrite: Whether to overwrite existing output file.

        Raises:
            TypeError: If arguments are of incorrect type.
            ValueError: If output format extension is unsupported.
            FileWriteError: If output file exists and overwrite is False.
            FFmpegNotFoundError: If FFmpeg executable is not found in PATH.
            FFmpegError: If FFmpeg encoding fails.
        """

    def _check_output_path(
        self,
        output_path: str | PathLike[str],
        supported_formats: Sequence[str],
        overwrite: bool,
    ) -> Path:
        """Validate and prepare the output destination path.

        Args:
            output_path: The target output file path.
            supported_formats: Sequence of supported file extension names.
            overwrite: Whether existing output files should be overwritten.

        Returns:
            Path: Validated Path object.

        Raises:
            TypeError: If arguments are of incorrect type.
            ValueError: If the file extension is not supported.
            FileWriteError: If output file already exists and overwrite is False,
                or if the existing file is not writable.
        """
        if not isinstance(output_path, (str, PathLike)):
            t_name = type(output_path).__name__
            raise TypeError(f"output_path must be a str or PathLike, got {t_name}")
        if not isinstance(overwrite, bool):
            raise TypeError(f"overwrite must be a bool, got {type(overwrite).__name__}")
        if not isinstance(supported_formats, Sequence):
            t_name = type(supported_formats).__name__
            raise TypeError(
                f"supported_formats must be a Sequence of str, got {t_name}"
            )

        path = Path(output_path)
        ext = path.suffix.lower().lstrip(".")
        allowed = [fmt.lower().lstrip(".") for fmt in supported_formats]

        if not ext or ext not in allowed:
            expected = [f".{fmt}" for fmt in allowed]
            msg = (
                f"Unsupported output file extension: '{path.suffix}'. "
                f"Expected one of: {expected}"
            )
            raise ValueError(msg)

        if path.exists() and not overwrite:
            raise FileWriteError(f"Output file already exists: {path}")

        if path.exists() and overwrite and not access(path, W_OK):
            raise FileWriteError(f"Output file is not writable: {path}")

        if not path.parent.exists():
            path.parent.mkdir(parents=True, exist_ok=True)

        return path

    def _run_ffmpeg_encode(
        self,
        codec_args: Sequence[str],
        pcm: PCM,
        output_path: Path | str | PathLike[str],
        overwrite: bool,
    ) -> None:
        """Run the FFmpeg encoding subprocess with piping and error handling.

        Args:
            codec_args: Encoder and codec-specific FFmpeg arguments.
            pcm: The PCM audio data to encode.
            output_path: Destination path for the output file.
            overwrite: Whether to overwrite existing file.

        Raises:
            TypeError: If arguments are of incorrect type.
            FFmpegNotFoundError: If FFmpeg executable is not found in PATH.
            FFmpegError: If FFmpeg encoding process fails.
        """
        if not isinstance(pcm, PCM):
            t_name = type(pcm).__name__
            raise TypeError(
                f"Invalid PCM data type: expected PCM instance, got {t_name}"
            )
        if not isinstance(overwrite, bool):
            raise TypeError(f"overwrite must be a bool, got {type(overwrite).__name__}")
        if not isinstance(codec_args, Sequence):
            t_name = type(codec_args).__name__
            raise TypeError(f"codec_args must be a Sequence of str, got {t_name}")
        if not isinstance(output_path, (str, PathLike)):
            t_name = type(output_path).__name__
            raise TypeError(f"output_path must be a str or PathLike, got {t_name}")

        cmd: list[str] = [
            "ffmpeg",
            "-y" if overwrite else "-n",
            "-f",
            pcm.format.value,
            "-ar",
            str(pcm.sample_rate.value),
            "-ac",
            str(pcm.channels.value),
            "-i",
            "pipe:0",
            *codec_args,
            "-loglevel",
            "error",
            str(output_path),
        ]

        try:
            subprocess.run(
                cmd,
                input=pcm.data,
                capture_output=True,
                check=True,
            )
        except OSError as e:
            if e.errno == 2:
                raise FFmpegNotFoundError(
                    "ffmpeg executable not found. Please ensure FFmpeg is in PATH."
                ) from e
            raise FFmpegError(f"Failed to start ffmpeg process: {e}") from e
        except subprocess.CalledProcessError as e:
            err_msg = (
                e.stderr.decode("utf-8", errors="ignore").strip()
                if isinstance(e.stderr, (bytes, bytearray))
                else str(e.stderr or "")
            )
            raise FFmpegError(
                f"FFmpeg failed to encode to {output_path}: {err_msg}",
                stderr=err_msg,
            ) from e


__all__ = ["BaseAudioEncoder"]
