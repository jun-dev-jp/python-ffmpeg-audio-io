"""AIFF encoder module using FFmpeg."""

from __future__ import annotations

from os import PathLike

from ..pcm import PCM, PCMCodec
from .base import BaseAudioEncoder

SUPPORTED_AIFF_FORMAT_NAMES = ["aiff", "aif"]


class AIFFEncoder(BaseAudioEncoder):
    """Encoder class for encoding PCM audio data to AIFF format using FFmpeg."""

    def __init__(
        self,
        codec: PCMCodec = PCMCodec.PCM_S16BE,
    ) -> None:
        if not isinstance(codec, PCMCodec):
            t_name = type(codec).__name__
            raise TypeError(f"codec must be an instance of PCMCodec, got {t_name}")
        self._codec: PCMCodec = codec

    def __call__(
        self,
        pcm: PCM,
        output_path: str | PathLike[str],
        overwrite: bool = False,
    ) -> None:
        """Encode PCM audio data to AIFF format and save to destination path.

        Args:
            pcm: PCM audio data to encode.
            output_path: Destination path for the encoded AIFF file.
            overwrite: Whether to overwrite existing output file.

        Raises:
            TypeError: If arguments are of incorrect type.
            ValueError: If output format extension is unsupported.
            FileWriteError: If output file exists and overwrite is False.
            FFmpegNotFoundError: If FFmpeg executable is not found in PATH.
            FFmpegError: If FFmpeg encoding fails.
        """
        dest_path = self._check_output_path(
            output_path, SUPPORTED_AIFF_FORMAT_NAMES, overwrite
        )

        codec_args: list[str] = [
            "-c:a",
            self._codec.value,
            "-f",
            "aiff",
        ]

        self._run_ffmpeg_encode(codec_args, pcm, dest_path, overwrite)

    @property
    def codec(self) -> PCMCodec:
        """Return the codec used for AIFF encoding."""
        return self._codec

    @codec.setter
    def codec(self, value: PCMCodec) -> None:
        """Set the codec of the AIFF encoder."""
        if not isinstance(value, PCMCodec):
            t_name = type(value).__name__
            raise TypeError(f"codec must be an instance of PCMCodec, got {t_name}")
        self._codec = value
