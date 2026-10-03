# python-ffmpeg-audio-io

## Project Overview
A lightweight and robust audio I/O library that directly wraps FFmpeg / FFprobe using Python's standard `subprocess` module to retrieve audio metadata, decode audio files, and encode them into various formats (MP3, AAC, AIFF, Opus, FLAC).

## Design Principles & Requirements
1. **Restrictions on External Packages**:
   - Do not use heavy third-party wrapper libraries (`ffmpeg-python`, `pydub`, etc.) for core audio processing; communicate directly with FFmpeg / FFprobe via the standard library (`subprocess`, etc.).
   - Use `numpy` for handling raw data and numerical arrays.
2. **Package & Environment Management**:
   - Use `uv` for dependency management, virtual environment setup, and running tests.
   - Target Python version: **Python 3.14** (compatible with 3.11+).
3. **Unified Interface**:
   - **Decoding**: Regardless of the input file format (MP3, WAV, AIFF, FLAC, AAC, etc.), decode to a `PCM` object holding raw PCM data via a unified API (`decode()` function).
   - **Metadata Extraction**: Retrieve audio metadata such as sample rate, channel count, bit rate, and duration via `get_audio_info()`.
   - **Encoding**: Format-specific encoder classes (`MP3Encoder`, `AACEncoder`, `AIFFEncoder`, `OpusEncoder`, `FLACEncoder`) inherit from `BaseAudioEncoder` and expose a unified call signature: `__call__(pcm, output_path, overwrite=False)`.
4. **Treating Audio Files as Streams**:
   - **Avoiding Temp Files & Leveraging Pipes**: Process raw PCM data sequentially as binary streams using FFmpeg process standard I/O pipes (`pipe:0`, `pipe:1`) without relying on temporary files on disk.
   - **Read Stream**: Provide a single reader (`AudioStreamReader`) that yields raw PCM chunks sequentially from an audio file (supports `with` context manager).
   - **Write Stream**:
     - Sequentially supply raw PCM chunks to FFmpeg's standard input (`pipe:0`) to perform format conversion.
     - **Restrict output destinations strictly to file paths**: Writing encoding output directly to disk files eliminates deadlock (hang) risks associated with OS pipe buffer overflows (~64KB), keeping the implementation simple and robust (in-memory stream output like `BytesIO` is out of scope).
     - Provide format-specific writer classes (`MP3StreamWriter`, `AACStreamWriter`, etc.) inheriting from `BaseAudioStreamWriter` (supports `with` context manager).

## Error Handling Policy
1. **Exception Hierarchy (All unified under `PyFFmpegAudioIOError`)**:
   - Base: `PyFFmpegAudioIOError` (all library-specific exceptions inherit from this; supports storing FFmpeg `stderr`)
   - Type and Value Validation:
     - `AudioTypeError`: Raised when an argument has an invalid type (inherits from `PyFFmpegAudioIOError` and `TypeError`).
     - `AudioValueError`: Raised when an argument has an invalid value (inherits from `PyFFmpegAudioIOError` and `ValueError`).
     - `PCMFormatError`: Raised when a PCM format is unsupported, invalid, or cannot be converted to/from NumPy (inherits from `AudioValueError`).
   - File & I/O:
     - `AudioIOError`: Base exception for file I/O operations (inherits from `PyFFmpegAudioIOError` and `OSError`).
     - `FileReadError`: File does not exist, lacks read permissions, or is not a regular file (inherits from `AudioIOError`).
     - `FileWriteError`: Destination file already exists and overwrite is disabled, or destination is not writable (inherits from `AudioIOError`).
   - FFmpeg Execution:
     - `FFmpegError`: FFmpeg or FFprobe subprocess execution terminates with an error (stores `stderr`).
     - `FFmpegNotFoundError`: FFmpeg or FFprobe executable is not found in system PATH (inherits from `FFmpegError` and `FileNotFoundError`).
   - Stream Processing:
     - `StreamError` (alias `AudioStreamError`): Base exception for stream processing.
       - `StreamClosedError`: I/O operations attempted on a closed or terminated stream.
       - `StreamBrokenError`: Unexpected termination of the FFmpeg process, broken pipe, or stream disconnection (inherits from `StreamError` and `BrokenPipeError`).
2. **FFmpeg Exception Wrapping**:
   - For operations involving external processes (`subprocess` calls to `ffmpeg` or `ffprobe`), always implement robust exception handling anticipating execution failures (`FileNotFoundError`/`OSError`, `CalledProcessError`, etc.).
   - On error, capture FFmpeg's standard error (`stderr`) output message and raise a clear library exception with `stderr` accessible on the exception object.
3. **Input Validation and Type Safety**:
   - All public API boundaries and methods must validate input argument types and values early.
   - Invalid argument types must raise `AudioTypeError`, and invalid values (unsupported extensions, invalid enum values, misaligned data) must raise `AudioValueError` (or `PCMFormatError`).

## Development & Quality Assurance
- **Static Type Checking**: Use Pyright (`uv run pyright`). Strictly adhere to PEP 561 (`py.typed`) and type annotations.
- **Docstrings**: All public APIs (modules, classes, functions, methods) must have Google-style docstrings (`Args`, `Returns`, `Raises`, etc.).
- **Linter / Formatter**: `uv run ruff check` / `uv run ruff format`
- **Testing**: `uv run pytest`
