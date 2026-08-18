"""PCM data structures and format enumerations."""

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum


class PCMFormat(Enum):
    """Enum for PCM audio format options."""

    U8 = "u8"
    S8 = "s8"
    U16BE = "u16be"
    U16LE = "u16le"
    S16BE = "s16be"
    S16LE = "s16le"
    U24BE = "u24be"
    U24LE = "u24le"
    S24BE = "s24be"
    S24LE = "s24le"
    U32BE = "u32be"
    U32LE = "u32le"
    S32BE = "s32be"
    S32LE = "s32le"
    F32BE = "f32be"
    F32LE = "f32le"
    F64BE = "f64be"
    F64LE = "f64le"
    S64BE = "s64be"
    S64LE = "s64le"
    U64BE = "u64be"
    U64LE = "u64le"


class PCMCodec(Enum):
    """Enum for PCM codec options."""

    PCM_U8 = "pcm_u8"
    PCM_S8 = "pcm_s8"
    PCM_U16BE = "pcm_u16be"
    PCM_U16LE = "pcm_u16le"
    PCM_S16BE = "pcm_s16be"
    PCM_S16LE = "pcm_s16le"
    PCM_U24BE = "pcm_u24be"
    PCM_U24LE = "pcm_u24le"
    PCM_S24BE = "pcm_s24be"
    PCM_S24LE = "pcm_s24le"
    PCM_U32BE = "pcm_u32be"
    PCM_U32LE = "pcm_u32le"
    PCM_S32BE = "pcm_s32be"
    PCM_S32LE = "pcm_s32le"
    PCM_F32BE = "pcm_f32be"
    PCM_F32LE = "pcm_f32le"
    PCM_F64BE = "pcm_f64be"
    PCM_F64LE = "pcm_f64le"
    PCM_S64BE = "pcm_s64be"
    PCM_S64LE = "pcm_s64le"
    PCM_U64BE = "pcm_u64be"
    PCM_U64LE = "pcm_u64le"

    @property
    def pcm_format(self) -> PCMFormat:
        """Return the corresponding PCMFormat for this codec."""
        fmt_str = self.value.removeprefix("pcm_")
        return PCMFormat(fmt_str)


class PCMSampleRate(Enum):
    """Enum for PCM sample rate options."""

    RATE_8K = 8000
    RATE_11K = 11025
    RATE_12K = 12000
    RATE_16K = 16000
    RATE_22K = 22050
    RATE_24K = 24000
    RATE_32K = 32000
    RATE_44K = 44100
    RATE_48K = 48000
    RATE_64K = 64000
    RATE_88K = 88200
    RATE_96K = 96000
    RATE_176K = 176400
    RATE_192K = 192000
    RATE_352K = 352800
    RATE_384K = 384000


class PCMChannels(Enum):
    """Enum for PCM channels."""

    MONO = 1
    STEREO = 2
    THREE = 3
    QUAD = 4
    FIVE_ONE = 6
    SEVEN_ONE = 8


@dataclass(frozen=True)
class PCM:
    """Dataclass holding raw PCM audio data and its format specifications."""

    data: bytes | bytearray
    format: PCMFormat
    sample_rate: PCMSampleRate
    channels: PCMChannels

    def __post_init__(self) -> None:
        """Validate fields upon initialization."""
        if not isinstance(self.data, (bytes, bytearray)):
            t_name = type(self.data).__name__
            raise TypeError(f"data must be bytes or bytearray, got {t_name}")
        if isinstance(self.data, bytearray):
            object.__setattr__(self, "data", bytes(self.data))
        if not isinstance(self.format, PCMFormat):
            t_name = type(self.format).__name__
            raise TypeError(f"format must be an instance of PCMFormat, got {t_name}")
        if not isinstance(self.sample_rate, PCMSampleRate):
            t_name = type(self.sample_rate).__name__
            raise TypeError(
                f"sample_rate must be an instance of PCMSampleRate, got {t_name}"
            )
        if not isinstance(self.channels, PCMChannels):
            t_name = type(self.channels).__name__
            raise TypeError(
                f"channels must be an instance of PCMChannels, got {t_name}"
            )
