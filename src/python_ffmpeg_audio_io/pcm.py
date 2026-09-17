"""PCM data structures and format enumerations."""

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
from logging import getLogger
from typing import Any

import numpy as np
from numpy.typing import NDArray

from .exceptions import AudioTypeError, AudioValueError, PCMFormatError

logger = getLogger(__name__)


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
    S64BE = "s64be"
    S64LE = "s64le"
    U64BE = "u64be"
    U64LE = "u64le"
    F64BE = "f64be"
    F64LE = "f64le"

    @property
    def bytes_per_sample(self) -> int:
        """Return the number of bytes per audio sample for this format."""
        val = self.value
        if val in ("u8", "s8"):
            return 1
        if val.startswith(("u16", "s16")):
            return 2
        if val.startswith(("u24", "s24")):
            return 3
        if val.startswith(("u32", "s32", "f32")):
            return 4
        if val.startswith(("u64", "s64", "f64")):
            return 8
        raise PCMFormatError(f"Unknown bytes per sample for format: {self.value}")


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
    PCM_S64BE = "pcm_s64be"
    PCM_S64LE = "pcm_s64le"
    PCM_U64BE = "pcm_u64be"
    PCM_U64LE = "pcm_u64le"
    PCM_F64BE = "pcm_f64be"
    PCM_F64LE = "pcm_f64le"

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
            raise AudioTypeError(f"data must be bytes or bytearray, got {t_name}")
        if isinstance(self.data, bytearray):
            object.__setattr__(self, "data", bytes(self.data))
        if not isinstance(self.format, PCMFormat):
            t_name = type(self.format).__name__
            raise AudioTypeError(
                f"format must be an instance of PCMFormat, got {t_name}"
            )
        if not isinstance(self.sample_rate, PCMSampleRate):
            t_name = type(self.sample_rate).__name__
            raise AudioTypeError(
                f"sample_rate must be an instance of PCMSampleRate, got {t_name}"
            )
        if not isinstance(self.channels, PCMChannels):
            t_name = type(self.channels).__name__
            raise AudioTypeError(
                f"channels must be an instance of PCMChannels, got {t_name}"
            )

        # Validate that total data byte length is aligned to whole audio frames
        frame_size = self.format.bytes_per_sample * self.channels.value
        if len(self.data) % frame_size != 0:
            msg = (
                f"PCM data length ({len(self.data)} bytes) is not aligned to frame "
                f"size ({frame_size} bytes = {self.format.bytes_per_sample} "
                f"bytes/sample * {self.channels.value} channels)"
            )
            raise AudioValueError(msg)

    @staticmethod
    def from_numpy(
        arr: NDArray[np.floating[Any] | np.integer[Any]],
        sample_rate: PCMSampleRate,
        channels: PCMChannels,
    ) -> PCM:
        """Initialize PCM from a NumPy array.

        Args:
            arr: The NumPy array to convert.
            sample_rate: The sample rate of the PCM data.
            channels: The number of channels in the PCM data.

        Returns:
            The PCM object initialized from the NumPy array.

        Raises:
            AudioTypeError: If arr, sample_rate, or channels has an invalid type.
            AudioValueError: If arr shape or dimension is invalid for channels.
            PCMFormatError: If the NumPy array dtype is not supported.
        """
        if not isinstance(arr, np.ndarray):
            t_name = type(arr).__name__
            raise AudioTypeError(f"arr must be a numpy.ndarray, got {t_name}")
        if not isinstance(sample_rate, PCMSampleRate):
            t_name = type(sample_rate).__name__
            raise AudioTypeError(
                f"sample_rate must be an instance of PCMSampleRate, got {t_name}"
            )
        if not isinstance(channels, PCMChannels):
            t_name = type(channels).__name__
            raise AudioTypeError(
                f"channels must be an instance of PCMChannels, got {t_name}"
            )

        if arr.ndim == 1:
            if arr.size % channels.value != 0:
                msg = (
                    f"Array size ({arr.size}) is not divisible by channel count "
                    f"({channels.value})"
                )
                raise AudioValueError(msg)
        elif arr.ndim == 2:
            if arr.shape[1] != channels.value:
                msg = (
                    f"Array channel count ({arr.shape[1]}) does not match channels "
                    f"({channels.value})"
                )
                raise AudioValueError(msg)
        else:
            raise AudioValueError(
                f"arr must be a 1D or 2D array, got {arr.ndim}D array"
            )

        native_dtype = arr.dtype.newbyteorder("=")
        if native_dtype == np.uint8:
            format = PCMFormat.U8
        elif native_dtype == np.int8:
            format = PCMFormat.S8
        elif native_dtype == np.uint16:
            format = PCMFormat.U16LE
        elif native_dtype == np.int16:
            format = PCMFormat.S16LE
        elif native_dtype == np.uint32:
            format = PCMFormat.U32LE
        elif native_dtype == np.int32:
            format = PCMFormat.S32LE
        elif native_dtype == np.float32:
            format = PCMFormat.F32LE
        elif native_dtype == np.uint64:
            format = PCMFormat.U64LE
        elif native_dtype == np.int64:
            format = PCMFormat.S64LE
        elif native_dtype == np.float64:
            format = PCMFormat.F64LE
        else:
            raise PCMFormatError(f"Unsupported Ndarray dtype: {arr.dtype}")

        contiguous_arr = np.ascontiguousarray(arr)
        if contiguous_arr.dtype.byteorder == ">":
            contiguous_arr = contiguous_arr.astype(
                contiguous_arr.dtype.newbyteorder("<")
            )

        return PCM(
            data=contiguous_arr.tobytes(),
            format=format,
            sample_rate=sample_rate,
            channels=channels,
        )

    def as_numpy(
        self,
    ) -> NDArray[
        np.uint8
        | np.int8
        | np.uint16
        | np.int16
        | np.uint32
        | np.int32
        | np.float32
        | np.uint64
        | np.int64
        | np.float64
    ]:
        """Convert PCM data to a NumPy array.

        Note:
            - u24LE, u24BE, s24LE, and s24BE are not supported.
            - Big-endian formats (e.g. u32BE, s32BE, f32BE, u64BE, s64BE) are
              converted to little-endian.

        Returns:
            The PCM data as a NumPy array with shape (num_samples, channels).

        Raises:
            PCMFormatError: If the PCM format is not supported.
        """
        format_val = self.format.value
        channels = self.channels.value

        if format_val == "u8":
            return np.frombuffer(self.data, dtype=np.uint8).reshape(-1, channels)
        elif format_val == "s8":
            return np.frombuffer(self.data, dtype=np.int8).reshape(-1, channels)
        elif format_val.startswith(("u24", "s24")):
            logger.error("Unsupported PCM format: %s", format_val)
            raise PCMFormatError(f"Unsupported PCM format: {format_val}")
        elif format_val.startswith("u16"):
            type_code = "u2"
        elif format_val.startswith("s16"):
            type_code = "i2"
        elif format_val.startswith("u32"):
            type_code = "u4"
        elif format_val.startswith("s32"):
            type_code = "i4"
        elif format_val.startswith("f32"):
            type_code = "f4"
        elif format_val.startswith("u64"):
            type_code = "u8"
        elif format_val.startswith("s64"):
            type_code = "i8"
        elif format_val.startswith("f64"):
            type_code = "f8"
        else:
            logger.error("Unsupported PCM format: %s", format_val)
            raise PCMFormatError(f"Unsupported PCM format: {format_val}")

        if format_val.endswith("le"):
            dtype = np.dtype(f"<{type_code}")
            return np.frombuffer(self.data, dtype=dtype).reshape(-1, channels)
        elif format_val.endswith("be"):
            be_dtype = np.dtype(f">{type_code}")
            le_dtype = np.dtype(f"<{type_code}")
            return (
                np.frombuffer(self.data, dtype=be_dtype)
                .astype(le_dtype)
                .reshape(-1, channels)
            )
        else:
            logger.error("Unsupported PCM format: %s", format_val)
            raise PCMFormatError(f"Unsupported PCM format: {format_val}")


__all__ = [
    "PCM",
    "PCMChannels",
    "PCMCodec",
    "PCMFormat",
    "PCMSampleRate",
]
