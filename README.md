# python-ffmpeg-audio-io

A lightweight, robust Python audio I/O library powered by FFmpeg and NumPy, designed without heavy third-party wrappers (`ffmpeg-python`, `pydub`, etc.).

## Features

- **Direct FFmpeg/FFprobe integration**: Uses standard library `subprocess` and FFmpeg for maximum reliability and flexibility.
- **NumPy native**: Seamlessly read audio streams directly into NumPy arrays and write NumPy arrays back to various audio formats.
- **Type-hinted & Robust**: Fully type-hinted with robust error handling (capturing detailed FFmpeg stderr messages).

## Requirements

- Python 3.13 or higher
- FFmpeg and FFprobe installed on your system and available in `PATH`.

## Installation

```bash
# Install directly from GitHub using uv or pip
uv pip install git+https://github.com/YOUR_USERNAME/python-ffmpeg-audio-io.git
```

## Quick Start

```python
import numpy as np
from python_ffmpeg_audio_io import AudioReader, AudioWriter  # Adjust based on your actual module structure

# Example usage goes here
```

## License

[MIT License](LICENSE)
