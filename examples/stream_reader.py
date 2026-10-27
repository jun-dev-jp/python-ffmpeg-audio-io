"""Example script demonstrating usage of AudioStreamReader."""

import argparse
from pathlib import Path

from python_ffmpeg_audio_io import (
    AudioStreamReader,
    FileReadError,
    PCMCodec,
    PyFFmpegAudioIOError,
)


def parse_args(args: list[str] | None = None) -> argparse.Namespace:
    """Parse command-line arguments.

    Args:
        args: Command-line arguments, or None to use sys.argv.

    Returns:
        Parsed command-line arguments.
    """
    parser = argparse.ArgumentParser(
        description="Read an audio file in chunks.",
        formatter_class=argparse.ArgumentDefaultsHelpFormatter,
    )
    parser.add_argument(
        "input_file",
        nargs="?",
        type=Path,
        default=Path("samples/sample.mp3"),
        help="Path to the input audio file",
    )
    return parser.parse_args(args)


def main(args: list[str] | None = None) -> None:
    """Stream-read the audio file specified on the command line."""
    parsed_args = parse_args(args)
    input_path: Path = parsed_args.input_file
    if not input_path.exists():
        print(f"Audio file not found at {input_path}")
        return

    print(f"Streaming audio file: {input_path}\n")

    try:
        # Read 4096 frames per chunk using 32-bit float PCM
        with AudioStreamReader(
            input_path,
            pcm_codec=PCMCodec.PCM_F32LE,
            chunk_frames=4096,
        ) as reader:
            print("Audio Metadata:")
            print(f"  - Codec: {reader.info.codec_name}")
            print(f"  - Sample Rate: {reader.sample_rate.value} Hz")
            print(f"  - Channels: {reader.channels.value} ({reader.channels.name})")
            print(f"  - Duration: {reader.info.duration:.2f} s")
            print(f"  - Frame size: {reader.frame_size} bytes")
            print(f"  - Chunk frames: {reader.chunk_frames}\n")

            total_frames = 0
            total_bytes = 0
            chunk_count = 0

            print("Reading stream chunks...")
            for chunk in reader:
                chunk_count += 1
                total_bytes += len(chunk.data)
                frames_in_chunk = len(chunk.data) // reader.frame_size
                total_frames += frames_in_chunk

                # Convert chunk directly to NumPy array for analysis/processing
                arr = chunk.as_numpy()

                # Print progress for the first 3 chunks and periodic intervals
                if chunk_count <= 3:
                    peak_amp = float(abs(arr).max()) if arr.size > 0 else 0.0
                    print(
                        f"  [Chunk {chunk_count:03d}] {frames_in_chunk} frames "
                        f"({len(chunk.data)} bytes), peak amp: {peak_amp:.4f}"
                    )

            print(f"  ... total {chunk_count} chunks read.")
            print("\nStream reading completed successfully!")
            print(f"  - Total chunks: {chunk_count}")
            print(f"  - Total frames: {total_frames}")
            print(f"  - Total PCM bytes: {total_bytes}")
            calculated_duration = total_frames / reader.sample_rate.value
            print(f"  - Calculated duration: {calculated_duration:.2f} s")

    except (FileReadError, PyFFmpegAudioIOError) as e:
        print(f"Error streaming audio: {e}")

    print("\nDone!")


if __name__ == "__main__":
    main()
