"""python-ffmpeg-audio-io package."""

from .decoder import decode_to_PCM_F32LE_with_ffmpeg
from .encoder.aac import (
    AACEncoder,
    AACEncoderBitrate,
    AACEncoderMode,
    AACEncoderQualityLevel,
)
from .encoder.aiff import (
    AIFFEncoder,
)
from .encoder.mp3 import (
    MP3Encoder,
    MP3EncoderBitrate,
    MP3EncoderMode,
    MP3EncoderQualityLevel,
)
from .exceptions import FFmpegError, PyFFmpegAudioIOError
from .ffprobe import get_audio_info_from_ffprobe, run_ffprobe

__all__ = [
    "AACEncoder",
    "AACEncoderBitrate",
    "AACEncoderMode",
    "AACEncoderQualityLevel",
    "AIFFEncoder",
    "FFmpegError",
    "MP3Encoder",
    "MP3EncoderBitrate",
    "MP3EncoderMode",
    "MP3EncoderQualityLevel",
    "PyFFmpegAudioIOError",
    "decode_to_PCM_F32LE_with_ffmpeg",
    "get_audio_info_from_ffprobe",
    "run_ffprobe",
]


def hello() -> str:
    return "Hello from python-ffmpeg-audio-io!"
