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
from .encoder.wav import (
    WAVEncoder,
)
from .exceptions import (
    AudioIOError,
    AudioStreamError,
    AudioTypeError,
    AudioValueError,
    FFmpegError,
    FFmpegNotFoundError,
    FileReadError,
    FileWriteError,
    PCMFormatError,
    PyFFmpegAudioIOError,
    StreamBrokenError,
    StreamClosedError,
    StreamError,
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
from .stream_reader import (
    AudioStreamReader,
)
from .stream_writer import (
    AACStreamWriter,
    AIFFStreamWriter,
    BaseAudioStreamWriter,
    FLACStreamWriter,
    MP3StreamWriter,
    OpusStreamWriter,
    WAVStreamWriter,
)

__all__ = [
    "PCM",
    "AACEncoder",
    "AACEncoderBitrate",
    "AACEncoderMode",
    "AACEncoderQualityLevel",
    "AACStreamWriter",
    "AIFFEncoder",
    "AIFFStreamWriter",
    "AudioIOError",
    "AudioInfo",
    "AudioStreamError",
    "AudioStreamReader",
    "AudioTypeError",
    "AudioValueError",
    "BaseAudioEncoder",
    "BaseAudioStreamWriter",
    "FFmpegError",
    "FFmpegNotFoundError",
    "FFprobeLogLevel",
    "FLACEncoder",
    "FLACEncoderCompressionLevel",
    "FLACStreamWriter",
    "FileReadError",
    "FileWriteError",
    "MP3Encoder",
    "MP3EncoderBitrate",
    "MP3EncoderMode",
    "MP3EncoderQualityLevel",
    "MP3StreamWriter",
    "OpusEncoder",
    "OpusEncoderApplication",
    "OpusEncoderBitrate",
    "OpusEncoderMode",
    "OpusStreamWriter",
    "PCMChannels",
    "PCMCodec",
    "PCMFormat",
    "PCMFormatError",
    "PCMSampleRate",
    "PyFFmpegAudioIOError",
    "StreamBrokenError",
    "StreamClosedError",
    "StreamError",
    "WAVEncoder",
    "WAVStreamWriter",
    "decode",
    "get_audio_info",
    "run_ffprobe",
]
