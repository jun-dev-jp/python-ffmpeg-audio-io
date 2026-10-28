"""AIFF encoder module using FFmpeg."""

from __future__ import annotations

from os import PathLike

from ..exceptions import AudioTypeError, AudioValueError
from ..pcm import PCM, PCMCodec
from .base import BaseAudioEncoder

SUPPORTED_AIFF_FORMAT_NAMES = ["aiff", "aif"]
SUPPORTED_AIFF_CODECS: tuple[PCMCodec, ...] = (
    PCMCodec.PCM_S16BE,
    PCMCodec.PCM_S24BE,
    PCMCodec.PCM_S32BE,
    PCMCodec.PCM_F32BE,
    PCMCodec.PCM_F64BE,
)
_SUPPORTED_AIFF_CODECS = frozenset(SUPPORTED_AIFF_CODECS)


def _validate_aiff_codec(codec: PCMCodec) -> None:
    if not isinstance(codec, PCMCodec):
        t_name = type(codec).__name__
        raise AudioTypeError(f"codec must be an instance of PCMCodec, got {t_name}")
    if codec not in _SUPPORTED_AIFF_CODECS:
        raise AudioValueError(f"Unsupported AIFF PCM codec: {codec.value}")


class AIFFEncoder(BaseAudioEncoder):
    """Encoder class for encoding PCM audio data to AIFF format using FFmpeg."""

    def __init__(
        self,
        codec: PCMCodec = PCMCodec.PCM_S16BE,
    ) -> None:
        """Initialize the AIFF encoder.

        Args:
            codec: Supported PCM codec for AIFF encoding.

        Raises:
            AudioTypeError: If codec is not a PCMCodec.
            AudioValueError: If codec is unsupported for AIFF.
        """
        _validate_aiff_codec(codec)
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
            AudioTypeError: If arguments are of incorrect type.
            AudioValueError: If the codec or output format extension is unsupported.
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
        """Set the codec of the AIFF encoder.

        Raises:
            AudioTypeError: If value is not a PCMCodec.
            AudioValueError: If value is unsupported for AIFF.
        """
        _validate_aiff_codec(value)
        self._codec = value


__all__ = [
    "SUPPORTED_AIFF_CODECS",
    "SUPPORTED_AIFF_FORMAT_NAMES",
    "AIFFEncoder",
]
