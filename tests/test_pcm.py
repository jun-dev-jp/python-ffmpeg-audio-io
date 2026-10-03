"""Unit tests for PCM data structures and NumPy conversion methods."""

from __future__ import annotations

from typing import Any, cast

import numpy as np
import pytest

from python_ffmpeg_audio_io.exceptions import PCMFormatError
from python_ffmpeg_audio_io.pcm import (
    PCM,
    PCMChannels,
    PCMCodec,
    PCMFormat,
    PCMSampleRate,
)


def test_pcm_initialization_and_validation() -> None:
    """Test basic PCM dataclass instantiation and type validation."""
    pcm = PCM(
        data=b"\x00\x00\x00\x00",
        format=PCMFormat.S16LE,
        sample_rate=PCMSampleRate.RATE_44K,
        channels=PCMChannels.STEREO,
    )
    assert pcm.data == b"\x00\x00\x00\x00"
    assert pcm.format == PCMFormat.S16LE
    assert pcm.sample_rate == PCMSampleRate.RATE_44K
    assert pcm.channels == PCMChannels.STEREO

    # bytearray is automatically converted to bytes
    pcm_ba = PCM(
        data=bytearray(b"\x01\x02"),
        format=PCMFormat.U8,
        sample_rate=PCMSampleRate.RATE_48K,
        channels=PCMChannels.STEREO,
    )
    assert isinstance(pcm_ba.data, bytes)
    assert pcm_ba.data == b"\x01\x02"

    # Frame alignment error (3 bytes for 2ch 16-bit PCM: 4 bytes/frame required)
    with pytest.raises(ValueError, match="not aligned to frame size"):
        _ = PCM(
            data=b"\x01\x02\x03",
            format=PCMFormat.S16LE,
            sample_rate=PCMSampleRate.RATE_44K,
            channels=PCMChannels.STEREO,
        )

    # TypeError on invalid data type
    with pytest.raises(TypeError, match="data must be bytes"):
        _ = PCM(
            data=cast(Any, [1, 2, 3]),
            format=PCMFormat.S16LE,
            sample_rate=PCMSampleRate.RATE_44K,
            channels=PCMChannels.STEREO,
        )

    # TypeError on invalid format type
    with pytest.raises(TypeError, match="format must be an instance of PCMFormat"):
        _ = PCM(
            data=b"\x00\x00\x00\x00",
            format=cast(Any, "s16le"),
            sample_rate=PCMSampleRate.RATE_44K,
            channels=PCMChannels.STEREO,
        )

    # TypeError on invalid sample_rate type
    with pytest.raises(
        TypeError, match="sample_rate must be an instance of PCMSampleRate"
    ):
        _ = PCM(
            data=b"\x00\x00\x00\x00",
            format=PCMFormat.S16LE,
            sample_rate=cast(Any, 44100),
            channels=PCMChannels.STEREO,
        )

    # TypeError on invalid channels type
    with pytest.raises(TypeError, match="channels must be an instance of PCMChannels"):
        _ = PCM(
            data=b"\x00\x00\x00\x00",
            format=PCMFormat.S16LE,
            sample_rate=PCMSampleRate.RATE_44K,
            channels=cast(Any, 2),
        )


def test_pcm_format_bytes_per_sample() -> None:
    """Test bytes_per_sample property on all PCMFormat entries."""
    assert PCMFormat.U8.bytes_per_sample == 1
    assert PCMFormat.S8.bytes_per_sample == 1
    assert PCMFormat.S16LE.bytes_per_sample == 2
    assert PCMFormat.U16BE.bytes_per_sample == 2
    assert PCMFormat.S24LE.bytes_per_sample == 3
    assert PCMFormat.U24BE.bytes_per_sample == 3
    assert PCMFormat.S32LE.bytes_per_sample == 4
    assert PCMFormat.F32LE.bytes_per_sample == 4
    assert PCMFormat.S64LE.bytes_per_sample == 8
    assert PCMFormat.F64BE.bytes_per_sample == 8


def test_pcm_codec_format_property() -> None:
    """Test that all PCMCodec entries map to their corresponding PCMFormat."""
    for codec in PCMCodec:
        fmt = codec.pcm_format
        assert isinstance(fmt, PCMFormat)
        assert codec.value == f"pcm_{fmt.value}"


@pytest.mark.parametrize(
    ("dtype", "expected_format"),
    [
        (np.uint8, PCMFormat.U8),
        (np.int8, PCMFormat.S8),
        (np.uint16, PCMFormat.U16LE),
        (np.int16, PCMFormat.S16LE),
        (np.uint32, PCMFormat.U32LE),
        (np.int32, PCMFormat.S32LE),
        (np.float32, PCMFormat.F32LE),
        (np.uint64, PCMFormat.U64LE),
        (np.int64, PCMFormat.S64LE),
        (np.float64, PCMFormat.F64LE),
    ],
)
def test_from_numpy_all_supported_dtypes(
    dtype: type[np.generic], expected_format: PCMFormat
) -> None:
    """Test from_numpy converts supported NumPy dtypes to expected PCMFormats."""
    arr = np.arange(10, dtype=dtype).reshape(-1, 2)
    pcm = PCM.from_numpy(
        arr,
        sample_rate=PCMSampleRate.RATE_44K,
        channels=PCMChannels.STEREO,
    )
    assert pcm.format == expected_format
    assert pcm.sample_rate == PCMSampleRate.RATE_44K
    assert pcm.channels == PCMChannels.STEREO
    assert pcm.data == arr.tobytes()


def test_from_numpy_1d_array() -> None:
    """Test from_numpy with 1D NumPy array."""
    # Mono 1D array
    arr_mono = np.array([10, 20, 30], dtype=np.int16)
    pcm_mono = PCM.from_numpy(
        arr_mono,
        sample_rate=PCMSampleRate.RATE_48K,
        channels=PCMChannels.MONO,
    )
    assert pcm_mono.channels == PCMChannels.MONO
    assert pcm_mono.data == arr_mono.tobytes()

    # Stereo interleaved 1D array
    arr_stereo = np.array([10, -10, 20, -20], dtype=np.int16)
    pcm_stereo = PCM.from_numpy(
        arr_stereo,
        sample_rate=PCMSampleRate.RATE_44K,
        channels=PCMChannels.STEREO,
    )
    assert pcm_stereo.channels == PCMChannels.STEREO
    assert pcm_stereo.data == arr_stereo.tobytes()


def test_from_numpy_non_contiguous_and_big_endian() -> None:
    """Test from_numpy with non-C-contiguous and big-endian arrays."""
    # Fortran-contiguous array
    arr_f = np.asfortranarray(np.array([[1.0, 2.0], [3.0, 4.0]], dtype=np.float32))
    pcm_f = PCM.from_numpy(
        arr_f,
        sample_rate=PCMSampleRate.RATE_44K,
        channels=PCMChannels.STEREO,
    )
    recovered = pcm_f.as_numpy()
    np.testing.assert_array_equal(recovered, arr_f)

    # Big-endian array
    arr_be = np.array([[100, 200], [300, 400]], dtype=">i2")
    pcm_be = PCM.from_numpy(
        arr_be,
        sample_rate=PCMSampleRate.RATE_44K,
        channels=PCMChannels.STEREO,
    )
    recovered_be = pcm_be.as_numpy()
    np.testing.assert_array_equal(recovered_be, arr_be)


def test_from_numpy_validation_errors() -> None:
    """Test validation errors in from_numpy."""
    valid_arr = np.zeros((10, 2), dtype=np.float32)

    # Invalid arr type (e.g. list instead of ndarray)
    with pytest.raises(TypeError, match=r"arr must be a numpy\.ndarray"):
        _ = PCM.from_numpy(
            cast(Any, [[1.0, 2.0], [3.0, 4.0]]),
            sample_rate=PCMSampleRate.RATE_44K,
            channels=PCMChannels.STEREO,
        )

    # Invalid sample_rate type
    with pytest.raises(
        TypeError, match="sample_rate must be an instance of PCMSampleRate"
    ):
        _ = PCM.from_numpy(
            valid_arr,
            sample_rate=cast(Any, 44100),
            channels=PCMChannels.STEREO,
        )

    # Invalid channels type
    with pytest.raises(TypeError, match="channels must be an instance of PCMChannels"):
        _ = PCM.from_numpy(
            valid_arr,
            sample_rate=PCMSampleRate.RATE_44K,
            channels=cast(Any, 2),
        )

    # 1D array length not divisible by channel count
    arr_1d = np.array([1, 2, 3], dtype=np.int16)
    with pytest.raises(ValueError, match="not divisible by channel count"):
        _ = PCM.from_numpy(
            arr_1d,
            sample_rate=PCMSampleRate.RATE_44K,
            channels=PCMChannels.STEREO,
        )

    # 2D array channel count mismatch
    arr_3ch = np.zeros((10, 3), dtype=np.float32)
    with pytest.raises(ValueError, match=r"channel count .* does not match"):
        _ = PCM.from_numpy(
            arr_3ch,
            sample_rate=PCMSampleRate.RATE_44K,
            channels=PCMChannels.STEREO,
        )

    # 3D array
    arr_3d = np.zeros((2, 2, 2), dtype=np.float32)
    with pytest.raises(ValueError, match="must be a 1D or 2D array"):
        _ = PCM.from_numpy(
            arr_3d,
            sample_rate=PCMSampleRate.RATE_44K,
            channels=PCMChannels.STEREO,
        )

    # Unsupported dtype (bool, complex, object)
    arr_complex = np.array([1 + 2j, 3 + 4j], dtype=np.complex64)
    with pytest.raises(PCMFormatError, match="Unsupported Ndarray dtype"):
        _ = PCM.from_numpy(
            cast(Any, arr_complex),
            sample_rate=PCMSampleRate.RATE_44K,
            channels=PCMChannels.STEREO,
        )


@pytest.mark.parametrize(
    "fmt",
    [
        PCMFormat.U8,
        PCMFormat.S8,
        PCMFormat.U16LE,
        PCMFormat.S16LE,
        PCMFormat.U32LE,
        PCMFormat.S32LE,
        PCMFormat.F32LE,
        PCMFormat.U64LE,
        PCMFormat.S64LE,
        PCMFormat.F64LE,
    ],
)
def test_roundtrip_from_and_as_numpy(fmt: PCMFormat) -> None:
    """Test round-trip conversion between NumPy array and PCM for all formats."""
    type_map = {
        PCMFormat.U8: np.uint8,
        PCMFormat.S8: np.int8,
        PCMFormat.U16LE: np.uint16,
        PCMFormat.S16LE: np.int16,
        PCMFormat.U32LE: np.uint32,
        PCMFormat.S32LE: np.int32,
        PCMFormat.F32LE: np.float32,
        PCMFormat.U64LE: np.uint64,
        PCMFormat.S64LE: np.int64,
        PCMFormat.F64LE: np.float64,
    }
    dtype = type_map[fmt]
    original = np.arange(12, dtype=dtype).reshape(-1, 2)
    pcm = PCM.from_numpy(
        original,
        sample_rate=PCMSampleRate.RATE_44K,
        channels=PCMChannels.STEREO,
    )
    result = pcm.as_numpy()
    assert result.shape == (6, 2)
    assert result.dtype == dtype
    np.testing.assert_array_equal(result, original)


@pytest.mark.parametrize(
    ("be_format", "dtype_be", "values"),
    [
        (PCMFormat.U16BE, ">u2", [256, 512, 1024, 2048]),
        (PCMFormat.S16BE, ">i2", [-1000, 1000, -2000, 2000]),
        (PCMFormat.U32BE, ">u4", [100000, 200000]),
        (PCMFormat.S32BE, ">i4", [-100000, 100000]),
        (PCMFormat.F32BE, ">f4", [1.5, -2.5, 3.25, -4.75]),
        (PCMFormat.U64BE, ">u8", [1000000000, 2000000000]),
        (PCMFormat.S64BE, ">i8", [-1000000000, 1000000000]),
        (PCMFormat.F64BE, ">f8", [1.23456789, -9.87654321]),
    ],
)
def test_as_numpy_big_endian(
    be_format: PCMFormat,
    dtype_be: str,
    values: list[int | float],
) -> None:
    """Test as_numpy converts big-endian formats to little-endian NumPy arrays."""
    raw_arr = np.array(values, dtype=dtype_be)
    pcm = PCM(
        data=raw_arr.tobytes(),
        format=be_format,
        sample_rate=PCMSampleRate.RATE_44K,
        channels=PCMChannels.STEREO,
    )
    arr = pcm.as_numpy()
    assert arr.shape == (len(values) // 2, 2)
    assert arr.dtype.byteorder in ("=", "<")
    expected = np.array(values, dtype=dtype_be).astype(arr.dtype).reshape(-1, 2)
    np.testing.assert_array_almost_equal(arr, expected)


@pytest.mark.parametrize(
    "unsupported_fmt",
    [
        PCMFormat.U24LE,
        PCMFormat.U24BE,
        PCMFormat.S24LE,
        PCMFormat.S24BE,
    ],
)
def test_as_numpy_unsupported_24bit_formats(unsupported_fmt: PCMFormat) -> None:
    """Test that 24-bit PCM formats raise PCMFormatError when calling as_numpy."""
    pcm = PCM(
        data=b"\x00" * 24,
        format=unsupported_fmt,
        sample_rate=PCMSampleRate.RATE_44K,
        channels=PCMChannels.STEREO,
    )
    with pytest.raises(PCMFormatError, match="Unsupported PCM format"):
        _ = pcm.as_numpy()


def test_as_numpy_empty_data() -> None:
    """Test as_numpy with empty PCM data."""
    pcm = PCM(
        data=b"",
        format=PCMFormat.F32LE,
        sample_rate=PCMSampleRate.RATE_44K,
        channels=PCMChannels.STEREO,
    )
    arr = pcm.as_numpy()
    assert arr.shape == (0, 2)
    assert arr.dtype == np.float32


def test_pcm_num_frames_and_duration() -> None:
    """Test num_frames and duration properties on PCM instances."""
    # 1. 1 second of 44.1kHz 16-bit Stereo PCM (2 channels * 2 bytes = 4 bytes/frame)
    sample_rate_44k = PCMSampleRate.RATE_44K
    frames_44k = 44100
    frame_size_s16_stereo = 4
    data_44k = b"\x00" * (frames_44k * frame_size_s16_stereo)

    pcm_1s = PCM(
        data=data_44k,
        format=PCMFormat.S16LE,
        sample_rate=sample_rate_44k,
        channels=PCMChannels.STEREO,
    )
    assert isinstance(pcm_1s.num_frames, int)
    assert pcm_1s.num_frames == 44100
    assert isinstance(pcm_1s.duration, float)
    assert pcm_1s.duration == pytest.approx(1.0)

    # 2. 0.1 second of 48kHz 32-bit float Mono PCM (1 channel * 4 bytes = 4 bytes/frame)
    sample_rate_48k = PCMSampleRate.RATE_48K
    frames_48k = 4800
    frame_size_f32_mono = 4
    data_48k = b"\x00" * (frames_48k * frame_size_f32_mono)

    pcm_01s = PCM(
        data=data_48k,
        format=PCMFormat.F32LE,
        sample_rate=sample_rate_48k,
        channels=PCMChannels.MONO,
    )
    assert pcm_01s.num_frames == 4800
    assert pcm_01s.duration == pytest.approx(0.1)

    # 3. 24-bit 6-channel (FIVE_ONE) at 96kHz (6 channels * 3 bytes = 18 bytes/frame)
    frames_96k = 9600
    frame_size_24_51 = 18
    data_96k = b"\x00" * (frames_96k * frame_size_24_51)

    pcm_51 = PCM(
        data=data_96k,
        format=PCMFormat.S24LE,
        sample_rate=PCMSampleRate.RATE_96K,
        channels=PCMChannels.FIVE_ONE,
    )
    assert pcm_51.num_frames == 9600
    assert pcm_51.duration == pytest.approx(0.1)

    # 4. Empty data (0 frames, 0.0 seconds)
    pcm_empty = PCM(
        data=b"",
        format=PCMFormat.F32LE,
        sample_rate=PCMSampleRate.RATE_44K,
        channels=PCMChannels.STEREO,
    )
    assert pcm_empty.num_frames == 0
    assert pcm_empty.duration == 0.0
