"""WAV encoder module using FFmpeg."""

from __future__ import annotations

from os import PathLike

from ..exceptions import AudioTypeError
from ..pcm import PCM, PCMCodec
from .base import BaseAudioEncoder

SUPPORTED_WAV_FORMAT_NAMES = ["wav", "wave"]


class WAVEncoder(BaseAudioEncoder):
    """Encoder class for encoding PCM audio data to WAV format using FFmpeg."""

    def __init__(
        self,
        codec: PCMCodec = PCMCodec.PCM_S16LE,
    ) -> None:
        """Initialize WAVEncoder.

        Args:
            codec: PCMCodec for WAV encoding (default: PCM_S16LE).

        Raises:
            AudioTypeError: If codec is not an instance of PCMCodec.
        """
        if not isinstance(codec, PCMCodec):
            t_name = type(codec).__name__
            raise AudioTypeError(f"codec must be an instance of PCMCodec, got {t_name}")
        self._codec: PCMCodec = codec

    def __call__(
        self,
        pcm: PCM,
        output_path: str | PathLike[str],
        overwrite: bool = False,
    ) -> None:
        """Encode PCM audio data to WAV format and save to destination path.

        Args:
            pcm: PCM audio data to encode.
            output_path: Destination path for the encoded WAV file.
            overwrite: Whether to overwrite existing output file.

        Raises:
            AudioTypeError: If arguments are of incorrect type.
            AudioValueError: If output format extension is unsupported.
            FileWriteError: If output file exists and overwrite is False.
            FFmpegNotFoundError: If FFmpeg executable is not found in PATH.
            FFmpegError: If FFmpeg encoding fails.
        """
        dest_path = self._check_output_path(
            output_path, SUPPORTED_WAV_FORMAT_NAMES, overwrite
        )

        codec_args: list[str] = [
            "-c:a",
            self._codec.value,
            "-f",
            "wav",
        ]

        self._run_ffmpeg_encode(codec_args, pcm, dest_path, overwrite)

    @property
    def codec(self) -> PCMCodec:
        """Return the codec used for WAV encoding."""
        return self._codec

    @codec.setter
    def codec(self, value: PCMCodec) -> None:
        """Set the codec of the WAV encoder."""
        if not isinstance(value, PCMCodec):
            t_name = type(value).__name__
            raise AudioTypeError(f"codec must be an instance of PCMCodec, got {t_name}")
        self._codec = value


__all__ = [
    "SUPPORTED_WAV_FORMAT_NAMES",
    "WAVEncoder",
]
