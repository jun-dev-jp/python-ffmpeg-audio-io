"""Audio stream writers using FFmpeg stdin pipe."""

from __future__ import annotations

from .aac import AACStreamWriter
from .aiff import AIFFStreamWriter
from .base import BaseAudioStreamWriter
from .flac import FLACStreamWriter
from .mp3 import MP3StreamWriter
from .opus import OpusStreamWriter
from .wav import WAVStreamWriter

__all__ = [
    "AACStreamWriter",
    "AIFFStreamWriter",
    "BaseAudioStreamWriter",
    "FLACStreamWriter",
    "MP3StreamWriter",
    "OpusStreamWriter",
    "WAVStreamWriter",
]
