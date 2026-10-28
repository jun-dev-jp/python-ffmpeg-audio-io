"""WAV audio stream writer module using FFmpeg."""

from __future__ import annotations

from collections.abc import Sequence
from os import PathLike

from ..encoder.wav import SUPPORTED_WAV_FORMAT_NAMES, _validate_wav_codec
from ..pcm import PCMChannels, PCMCodec, PCMFormat, PCMSampleRate
from .base import BaseAudioStreamWriter


class WAVStreamWriter(BaseAudioStreamWriter):
    """Stream writer for encoding PCM audio data to WAV format using FFmpeg.

    Attributes:
        codec: PCMCodec used for the WAV container.
    """

    _codec: PCMCodec

    def __init__(
        self,
        output_path: str | PathLike[str],
        sample_rate: PCMSampleRate = PCMSampleRate.RATE_44K,
        channels: PCMChannels = PCMChannels.STEREO,
        pcm_format: PCMFormat = PCMFormat.F32LE,
        overwrite: bool = False,
        codec: PCMCodec = PCMCodec.PCM_S16LE,
    ) -> None:
        """Initialize WAVStreamWriter.

        Args:
            output_path: Destination path for the WAV file.
            sample_rate: Sample rate of the incoming PCM stream (default: 44.1kHz).
            channels: Channel count of the incoming PCM stream (default: Stereo).
            pcm_format: PCM format of incoming audio (default: F32LE).
            overwrite: Whether to overwrite existing file (default: False).
            codec: Audio PCMCodec for WAV encoding (default: PCM_S16LE).

        Raises:
            AudioTypeError: If arguments are of incorrect type.
            AudioValueError: If the codec, sample rate, channels, or output file
                extension is unsupported.
            FileWriteError: If output file exists and overwrite is False.
            FFmpegNotFoundError: If FFmpeg executable is not in PATH.
            FFmpegError: If FFmpeg fails to start.
        """
        _validate_wav_codec(codec)
        self._codec = codec

        super().__init__(
            output_path=output_path,
            sample_rate=sample_rate,
            channels=channels,
            pcm_format=pcm_format,
            overwrite=overwrite,
        )

    @property
    def supported_formats(self) -> Sequence[str]:
        """Return supported file extension names for WAV."""
        return SUPPORTED_WAV_FORMAT_NAMES

    def _get_codec_args(self) -> Sequence[str]:
        """Return WAV codec arguments for FFmpeg."""
        return [
            "-c:a",
            self._codec.value,
            "-f",
            "wav",
        ]

    @property
    def codec(self) -> PCMCodec:
        """Return the PCM codec used for WAV encoding."""
        return self._codec


__all__ = ["WAVStreamWriter"]
