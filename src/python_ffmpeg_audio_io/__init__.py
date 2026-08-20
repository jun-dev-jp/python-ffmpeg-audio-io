"""python-ffmpeg-audio-io package."""

from __future__ import annotations

from .decoder import decode
from .encoder.aac import (
    AACEncoder,
    AACEncoderBitrate,
    AACEncoderMode,
    AACEncoderQualityLevel,
)
from .encoder.aiff import (
    AIFFEncoder,
)
from .encoder.base import (
    BaseAudioEncoder,
)
from .encoder.flac import (
    FLACEncoder,
    FLACEncoderCompressionLevel,
)
from .encoder.mp3 import (
    MP3Encoder,
    MP3EncoderBitrate,
    MP3EncoderMode,
    MP3EncoderQualityLevel,
)
from .encoder.opus import (
    OpusEncoder,
    OpusEncoderApplication,
    OpusEncoderBitrate,
    OpusEncoderMode,
)
from .exceptions import (
    FFmpegError,
    FFmpegNotFoundError,
    FileReadError,
    FileWriteError,
    PCMFormatError,
    PyFFmpegAudioIOError,
)
from .ffprobe import (
    AudioInfo,
    FFprobeLogLevel,
    get_audio_info,
    run_ffprobe,
)
from .pcm import (
    PCM,
    PCMChannels,
    PCMCodec,
    PCMFormat,
    PCMSampleRate,
)

__all__ = [
    "PCM",
    "AACEncoder",
    "AACEncoderBitrate",
    "AACEncoderMode",
    "AACEncoderQualityLevel",
    "AIFFEncoder",
    "AudioInfo",
    "BaseAudioEncoder",
    "FFmpegError",
    "FFmpegNotFoundError",
    "FFprobeLogLevel",
    "FLACEncoder",
    "FLACEncoderCompressionLevel",
    "FileReadError",
    "FileWriteError",
    "MP3Encoder",
    "MP3EncoderBitrate",
    "MP3EncoderMode",
    "MP3EncoderQualityLevel",
    "OpusEncoder",
    "OpusEncoderApplication",
    "OpusEncoderBitrate",
    "OpusEncoderMode",
    "PCMChannels",
    "PCMCodec",
    "PCMFormat",
    "PCMFormatError",
    "PCMSampleRate",
    "PyFFmpegAudioIOError",
    "decode",
    "get_audio_info",
    "run_ffprobe",
]
