"""Example script demonstrating AIFF encoding with command-line arguments."""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

from python_ffmpeg_audio_io.decoder import decode
from python_ffmpeg_audio_io.encoder.aiff import SUPPORTED_AIFF_CODECS, AIFFEncoder
from python_ffmpeg_audio_io.exceptions import PyFFmpegAudioIOError
from python_ffmpeg_audio_io.pcm import PCMCodec

OUTPUT_DIR = Path("examples/outputs")


def parse_args(args: list[str] | None = None) -> argparse.Namespace:
    """Parse command-line arguments for AIFF encoding.

    Args:
        args: List of command-line argument strings, or None to use sys.argv.

    Returns:
        argparse.Namespace: Parsed command-line arguments.
    """
    parser = argparse.ArgumentParser(
        description="Encode an audio file to AIFF with custom parameters.",
        formatter_class=argparse.ArgumentDefaultsHelpFormatter,
    )
    parser.add_argument(
        "input_file",
        nargs="?",
        type=Path,
        default=Path("samples/65_BPM93.mp3"),
        help="Path to input audio file",
    )
    parser.add_argument(
        "-c",
        "--codec",
        type=str.lower,
        choices=[codec.value for codec in SUPPORTED_AIFF_CODECS],
        default="pcm_s16be",
        help="PCM codec for AIFF encoding",
    )
    parser.add_argument(
        "--overwrite",
        action=argparse.BooleanOptionalAction,
        default=True,
        help="Overwrite output file if it already exists",
    )
    return parser.parse_args(args)


def main() -> None:
    """Run AIFF encoding with command-line arguments."""
    args = parse_args()
    input_path: Path = args.input_file

    if not input_path.exists():
        print(f"Error: Input file not found at '{input_path}'", file=sys.stderr)
        sys.exit(1)

    codec_enum = PCMCodec(args.codec)
    output_filename = f"{input_path.stem}_{codec_enum.value}.aiff"
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    output_path = OUTPUT_DIR / output_filename

    print(f"Input file:  {input_path}")
    print(f"Output file: {output_path}")
    print("Format:      AIFF")
    print(f"PCM Codec:   {codec_enum.value}")

    print("\nDecoding input audio...")
    try:
        pcm = decode(input_path, PCMCodec.PCM_F32LE)
        print("Decoded PCM audio:")
        print(f"  - Sample Rate: {pcm.sample_rate.value} Hz")
        print(f"  - Channels:    {pcm.channels.value} ({pcm.channels.name})")
        print(f"  - Data Size:   {len(pcm.data):,} bytes")
    except PyFFmpegAudioIOError as e:
        print(f"Error decoding audio: {e}", file=sys.stderr)
        sys.exit(1)

    print("\nEncoding to AIFF...")
    encoder = AIFFEncoder(codec=codec_enum)

    try:
        encoder(pcm, output_path, overwrite=args.overwrite)
        file_size_kb = output_path.stat().st_size / 1024
        print(f"Encoding successful: {output_path} ({file_size_kb:.1f} KB)")
    except PyFFmpegAudioIOError as e:
        print(f"Error encoding audio: {e}", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()
