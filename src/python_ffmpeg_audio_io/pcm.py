from enum import Enum


class PCMFormat(Enum):
    """Enum for PCM audio format options."""

    S16BE = "s16be"
    S16LE = "s16le"
    S24BE = "s24be"
    S24LE = "s24le"
    S32BE = "s32be"
    S32LE = "s32le"
    F32BE = "f32be"
    F32LE = "f32le"


class PCMCodec(Enum):
    """Enum for PCM codec options."""

    PCM_S16BE = "pcm_s16be"
    PCM_S16LE = "pcm_s16le"
    PCM_S24BE = "pcm_s24be"
    PCM_S24LE = "pcm_s24le"
    PCM_S32BE = "pcm_s32be"
    PCM_S32LE = "pcm_s32le"
    PCM_F32BE = "pcm_f32be"
    PCM_F32LE = "pcm_f32le"


class PCMSampleRate(Enum):
    """Enum for PCM sample rate options."""

    RATE_8K = 8000
    RATE_16K = 16000
    RATE_22K = 22050
    RATE_32K = 32000
    RATE_44K = 44100
    RATE_48K = 48000
    RATE_88K = 88200
    RATE_96K = 96000
    RATE_176K = 176400
    RATE_192K = 192000


class PCMChannels(Enum):
    """Enum for PCM channels."""

    MONO = 1
    STEREO = 2
