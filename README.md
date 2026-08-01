# python-ffmpeg-audio-io

A lightweight, robust Python audio I/O library powered by FFmpeg, designed without heavy third-party wrappers (`ffmpeg-python`, `pydub`, etc.).

## Features

- **Direct FFmpeg/FFprobe integration**: Uses standard library `subprocess` and FFmpeg for maximum reliability and flexibility.
- **Type-hinted & Robust**: Fully type-hinted with robust error handling (capturing detailed FFmpeg stderr messages).
- **Supported Encoders**: Currently supports encoding to **MP3**, **AAC**, and **AIFF**.

## Requirements

- Python 3.13 or higher
- FFmpeg and FFprobe installed on your system and available in `PATH`.

## Installation

```bash
# Install directly from GitHub using uv or pip (HTTPS)
uv pip install git+https://github.com/YOUR_USERNAME/python-ffmpeg-audio-io.git

# Or using SSH
uv pip install git+ssh://git@github.com/YOUR_USERNAME/python-ffmpeg-audio-io.git

# To add it as a dependency to your uv project:
uv add git+https://github.com/YOUR_USERNAME/python-ffmpeg-audio-io.git
uv add git+ssh://git@github.com/YOUR_USERNAME/python-ffmpeg-audio-io.git
```

## Quick Start

```python
from pathlib import Path
from python_ffmpeg_audio_io import (
    decode_to_PCM_F32LE_with_ffmpeg,
    MP3Encoder,
    MP3EncoderBitrate,
    MP3EncoderMode,
)
from python_ffmpeg_audio_io.pcm import PCMFormat

# 1. Decode an audio file to raw PCM bytes
audio_path = Path("samples/sample.mp3")
pcm_data, sample_rate, channels = decode_to_PCM_F32LE_with_ffmpeg(audio_path)

# 2. Encode PCM bytes to MP3
encoder = MP3Encoder(bitrate=MP3EncoderBitrate.Kbps_192, mode=MP3EncoderMode.CBR)
output_path = Path("output.mp3")
encoder(pcm_data, PCMFormat.F32LE, sample_rate, channels, output_path, overwrite=True)
print(f"Successfully encoded to {output_path}")
```

## License

[MIT License](LICENSE)
