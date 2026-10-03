# python-ffmpeg-audio-io

[![CI](https://github.com/jun-dev-jp/python-ffmpeg-audio-io/actions/workflows/tests.yml/badge.svg)](https://github.com/jun-dev-jp/python-ffmpeg-audio-io/actions/workflows/tests.yml)
[![License: MIT](https://img.shields.io/badge/License-MIT-blue.svg)](https://opensource.org/licenses/MIT)
[![Python 3.11+](https://img.shields.io/badge/python-3.11+-blue.svg)](https://www.python.org/downloads/)

A lightweight, robust Python audio I/O library powered by FFmpeg, designed without heavy third-party wrappers (`ffmpeg-python`, `pydub`, etc.).

## Features

- **Direct FFmpeg/FFprobe Integration**: Uses standard library `subprocess` and FFmpeg pipes for maximum performance, reliability, and minimal overhead.
- **Unified Decoding API**: Decode diverse audio formats (MP3, AAC, AIFF, WAV, FLAC, OGG, etc.) into a structured `PCM` object with a single `decode()` function.
- **Dedicated Audio Encoders**: High-level batch encoders for **MP3**, **AAC**, **AIFF**, **Opus**, and **FLAC** supporting configurable bitrates, compression levels, and modes.
- **Streaming Audio I/O**:
  - **`AudioStreamReader`**: Stream audio decoding chunk-by-chunk using standard FFmpeg pipes without intermediate files.
  - **`StreamWriter`** (`MP3StreamWriter`, `AACStreamWriter`, `AIFFStreamWriter`, `OpusStreamWriter`, `FLACStreamWriter`): Incrementally feed PCM chunks directly into FFmpeg encoding processes.
- **NumPy Integration**: Seamlessly convert between `PCM` objects and `numpy.ndarray` via `pcm.as_numpy()` and `PCM.from_numpy()`.
- **Strict Typing & Runtime Validation**: Fully type-hinted (PEP 561 `py.typed`, verified with Pyright) with comprehensive runtime parameter validation.
- **Robust Error Handling**: Captures FFmpeg `stderr` and maps failures to a structured hierarchy derived from `PyFFmpegAudioIOError`.

## Requirements

- Python 3.14+
- FFmpeg and FFprobe installed on your system and available in `PATH`

## Installation

```bash
# Using uv
uv add git+https://github.com/jun-dev-jp/python-ffmpeg-audio-io.git

# Using pip
pip install git+https://github.com/jun-dev-jp/python-ffmpeg-audio-io.git
```

## Quick Start

### 1. Inspect Audio Metadata (`get_audio_info`)

```python
from python_ffmpeg_audio_io import get_audio_info

info = get_audio_info("samples/sample.mp3")
print(f"Sample Rate: {info.sample_rate} Hz")
print(f"Channels:    {info.channels}")
print(f"Duration:    {info.duration:.2f} s")
print(f"Codec:       {info.codec_name}")
print(f"Bitrate:     {info.bit_rate} bps")
```

### 2. Decode Audio to PCM (`decode`)

```python
from python_ffmpeg_audio_io import PCMCodec, decode

# Decode any supported audio file to raw PCM bytes (default: 32-bit float LE)
pcm = decode("samples/sample.mp3", pcm_codec=PCMCodec.PCM_F32LE)

print(f"Format:           {pcm.format.value}")  # e.g., 'f32le'
print(f"Sample Rate:      {pcm.sample_rate.value}")  # e.g., 44100
print(f"Channels:         {pcm.channels.value}")  # e.g., 2 (STEREO)
print(f"Raw Bytes Length: {len(pcm.data)}")
```

### 3. NumPy Interoperability (`as_numpy` / `from_numpy`)

```python
import numpy as np
from python_ffmpeg_audio_io import PCM, PCMChannels, PCMSampleRate, decode

# Decode and convert to a NumPy 2D array of shape (frames, channels)
pcm = decode("samples/sample.mp3")
arr = pcm.as_numpy()
print(f"NumPy array shape: {arr.shape}, dtype: {arr.dtype}")

# Manipulate audio samples (e.g., reduce volume by half)
arr = arr * 0.5

# Reconstruct a PCM object from the NumPy array
new_pcm = PCM.from_numpy(
    arr,
    sample_rate=PCMSampleRate.RATE_44K,
    channels=PCMChannels.STEREO,
)
```

### 4. Batch Audio Encoders

#### MP3 (`MP3Encoder`)

```python
from python_ffmpeg_audio_io import (
    MP3Encoder,
    MP3EncoderBitrate,
    MP3EncoderMode,
    MP3EncoderQualityLevel,
)

# CBR (Constant Bitrate)
encoder_cbr = MP3Encoder(bitrate=MP3EncoderBitrate.Kbps_192, mode=MP3EncoderMode.CBR)
encoder_cbr(pcm, "output_cbr.mp3", overwrite=True)

# VBR (Variable Bitrate: Quality_0 best ~ Quality_9 worst)
encoder_vbr = MP3Encoder(
    quality=MP3EncoderQualityLevel.Quality_2, mode=MP3EncoderMode.VBR
)
encoder_vbr(pcm, "output_vbr.mp3", overwrite=True)
```

#### AAC (`AACEncoder`)

```python
from python_ffmpeg_audio_io import (
    AACEncoder,
    AACEncoderBitrate,
    AACEncoderMode,
    AACEncoderQualityLevel,
)

# CBR (e.g. 128 kbps M4A/AAC)
encoder_aac = AACEncoder(bitrate=AACEncoderBitrate.Kbps_128, mode=AACEncoderMode.CBR)
encoder_aac(pcm, "output.m4a", overwrite=True)

# VBR (Quality_0 worst ~ Quality_5 best)
encoder_aac_vbr = AACEncoder(
    quality=AACEncoderQualityLevel.Quality_5, mode=AACEncoderMode.VBR
)
encoder_aac_vbr(pcm, "output_vbr.aac", overwrite=True)
```

#### AIFF (`AIFFEncoder`)

```python
from python_ffmpeg_audio_io import AIFFEncoder, PCMCodec

# Encode to 16-bit or 24-bit big-endian PCM in AIFF container
encoder_aiff = AIFFEncoder(codec=PCMCodec.PCM_S16BE)
encoder_aiff(pcm, "output.aiff", overwrite=True)
```

#### Opus (`OpusEncoder`)

```python
from python_ffmpeg_audio_io import (
    OpusEncoder,
    OpusEncoderApplication,
    OpusEncoderBitrate,
    OpusEncoderMode,
)

# VBR (Variable Bitrate: default)
encoder_opus = OpusEncoder(
    bitrate=OpusEncoderBitrate.Kbps_128,
    mode=OpusEncoderMode.VBR,
    application=OpusEncoderApplication.AUDIO,
)
encoder_opus(pcm, "output.opus", overwrite=True)
```

#### FLAC (`FLACEncoder`)

```python
from python_ffmpeg_audio_io import FLACEncoder, FLACEncoderCompressionLevel

# Lossless FLAC encoding with compression level 0 (fastest) ~ 12 (highest)
encoder_flac = FLACEncoder(compression_level=FLACEncoderCompressionLevel.Level_5)
encoder_flac(pcm, "output.flac", overwrite=True)
```

### 5. Stream Audio Decoding (`AudioStreamReader`)

Read audio chunks sequentially as `PCM` instances without loading the entire file into memory:

```python
from python_ffmpeg_audio_io import AudioStreamReader, PCMCodec

with AudioStreamReader(
    "samples/sample.mp3",
    pcm_codec=PCMCodec.PCM_F32LE,
    chunk_frames=4096,
) as reader:
    print(f"Sample Rate: {reader.sample_rate.value} Hz")
    print(f"Channels:    {reader.channels.value}")

    for pcm_chunk in reader:
        arr = pcm_chunk.as_numpy()
        print(f"Read chunk with {len(arr)} frames")
```

#### Detecting End of Stream (EOF) & Stream Status

You can detect when the audio stream has ended or closed:

- **Iterator (`for chunk in reader`)**: Automatically terminates when reaching the end of the audio stream (EOF).
- **Manual Read (`reader.read()`)**: Returns `None` once EOF is reached.
- **Raw Bytes Read (`reader.read_bytes()`)**: Returns an empty byte sequence `b""` on EOF.
- **Stream Status (`reader.closed`)**: A boolean property indicating whether the stream has been closed (e.g., after exiting the `with` block or explicitly calling `reader.close()`). Calling `read()` on a closed stream raises `StreamClosedError`.

```python
with AudioStreamReader("samples/sample.mp3") as reader:
    while True:
        chunk = reader.read()
        if chunk is None:
            print("Reached End of Stream (EOF)")
            break
        # Process chunk...

print(f"Stream closed: {reader.closed}")  # True
```

### 6. Stream Audio Encoding (`StreamWriter`)

Incrementally encode audio chunks directly to an output file. Stream writers are available for all supported formats (`MP3StreamWriter`, `AACStreamWriter`, `AIFFStreamWriter`, `OpusStreamWriter`, `FLACStreamWriter`).

```python
from python_ffmpeg_audio_io import (
    AudioStreamReader,
    MP3EncoderBitrate,
    MP3StreamWriter,
    PCMCodec,
)

# Stream read from source and stream encode directly to MP3 chunk-by-chunk
with AudioStreamReader(
    "samples/sample.wav",
    pcm_codec=PCMCodec.PCM_F32LE,
    chunk_frames=4096,
) as reader:
    with MP3StreamWriter(
        "output.mp3",
        sample_rate=reader.sample_rate,
        channels=reader.channels,
        pcm_format=reader.pcm_format,
        bitrate=MP3EncoderBitrate.Kbps_192,
        overwrite=True,
    ) as writer:
        for chunk in reader:
            writer.write(chunk)

    print(f"Frames written: {writer.frames_written}")
    print(f"Bytes written:  {writer.bytes_written}")
```

You can also pass raw audio bytes via `writer.write_bytes(raw_bytes)`.

## Exception Hierarchy

All library exceptions inherit from `PyFFmpegAudioIOError`, allowing callers to catch any library-specific error with a single base class. Where appropriate, they also inherit from standard Python exceptions (`TypeError`, `ValueError`, `OSError`) for seamless interoperability:

```
PyFFmpegAudioIOError
├── AudioTypeError           (Invalid argument type; inherits TypeError)
├── AudioValueError          (Invalid argument value; inherits ValueError)
│   └── PCMFormatError       (Unsupported or misaligned PCM format)
├── AudioIOError             (File/IO operations; inherits OSError)
│   ├── FileReadError        (Missing, unreadable, or non-file input)
│   └── FileWriteError       (Existing file without overwrite, or unwritable target)
├── FFmpegError              (Subprocess execution failure with captured stderr)
│   └── FFmpegNotFoundError  (FFmpeg or FFprobe not found in system PATH; inherits FileNotFoundError)
└── StreamError              (Base for streaming errors; alias: AudioStreamError)
    ├── StreamClosedError    (Operation on a closed stream)
    └── StreamBrokenError    (Pipe disconnect or unexpected process termination; inherits BrokenPipeError)
```

## Development

```bash
# Run tests
uv run pytest

# Check code formatting & linting
uv run ruff check
uv run ruff format

# Static type checking
uv run pyright
```

## License

[MIT License](LICENSE)
