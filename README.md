# python-ffmpeg-audio-io

A lightweight, robust Python audio I/O library powered by FFmpeg, designed without heavy third-party wrappers (`ffmpeg-python`, `pydub`, etc.).

## Features

- **Direct FFmpeg/FFprobe Integration**: Uses the standard library `subprocess` and FFmpeg pipes for maximum performance, reliability, and minimal overhead.
- **Unified Decoding API**: Decode diverse audio formats (MP3, AAC, AIFF, WAV, FLAC, etc.) into a structured `PCM` object with a single `decode()` function.
- **Dedicated Audio Encoders**: High-level encoders for **MP3**, **AAC**, and **AIFF** supporting CBR, ABR, and VBR modes.
- **Strict Typing & Runtime Validation**: Fully type-hinted (PEP 561 `py.typed`) with runtime parameter validation.
- **Robust Error Handling**: Captures FFmpeg `stderr` and maps failures to a structured hierarchy derived from `PyFFmpegAudioIOError`.

## Requirements

- Python 3.13 or higher (tested on Python 3.14)
- FFmpeg and FFprobe installed on your system and available in `PATH`

## Installation

```bash
# Using uv (HTTPS)
uv add git+https://github.com/YOUR_USERNAME/python-ffmpeg-audio-io.git

# Using pip
pip install git+https://github.com/YOUR_USERNAME/python-ffmpeg-audio-io.git
```

## Quick Start

### 1. Inspect Audio Metadata (`get_audio_info`)

```python
from pathlib import Path
from python_ffmpeg_audio_io import get_audio_info

info = get_audio_info("samples/sample.mp3")
print(f"Sample Rate: {info.sample_rate} Hz")
print(f"Channels: {info.channels}")
print(f"Duration: {info.duration:.2f} s")
print(f"Codec: {info.codec_name}")
print(f"Bitrate: {info.bit_rate} bps")
```

### 2. Decode Audio to PCM (`decode`)

```python
from pathlib import Path
from python_ffmpeg_audio_io import PCMCodec, decode

# Decode any supported audio file to raw PCM bytes (default: 32-bit float LE)
pcm = decode("samples/sample.mp3", pcm_codec=PCMCodec.PCM_F32LE)

print(f"Format: {pcm.format.value}")  # e.g., 'f32le'
print(f"Sample Rate: {pcm.sample_rate.value}")  # e.g., 44100
print(f"Channels: {pcm.channels.value}")  # e.g., 1 (MONO)
print(f"Raw Bytes Length: {len(pcm.data)}")
```

### 3. Encode to MP3 (`MP3Encoder`)

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

### 4. Encode to AAC (`AACEncoder`)

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

### 5. Encode to AIFF (`AIFFEncoder`)

```python
from python_ffmpeg_audio_io import AIFFEncoder, PCMCodec

# Encode to 16-bit or 24-bit big-endian PCM in AIFF container
encoder_aiff = AIFFEncoder(codec=PCMCodec.PCM_S16BE)
encoder_aiff(pcm, "output.aiff", overwrite=True)
```

## Exception Hierarchy

All library exceptions inherit from `PyFFmpegAudioIOError`:

```
PyFFmpegAudioIOError
├── FileReadError         (Missing, unreadable, or non-file input)
├── FileWriteError        (Existing file without overwrite, or unwritable target)
├── FFmpegError           (Subprocess execution failure with captured stderr)
└── FFmpegNotFoundError   (FFmpeg or FFprobe not found in system PATH)
```

## Development

```bash
# Run tests
uv run pytest

# Check code formatting & lint
uv run ruff check
uv run ruff format
```

## License

[MIT License](LICENSE)
