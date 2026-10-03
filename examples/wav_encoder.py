"""Example script demonstrating WAV encoding with command-line arguments."""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

from python_ffmpeg_audio_io.decoder import decode
from python_ffmpeg_audio_io.encoder.wav import WAVEncoder
from python_ffmpeg_audio_io.exceptions import PyFFmpegAudioIOError
from python_ffmpeg_audio_io.pcm import PCMCodec

WAV_SUPPORTED_CODECS: dict[str, PCMCodec] = {
    "pcm_s16le": PCMCodec.PCM_S16LE,
    "pcm_s24le": PCMCodec.PCM_S24LE,
    "pcm_s32le": PCMCodec.PCM_S32LE,
    "pcm_f32le": PCMCodec.PCM_F32LE,
    "pcm_f64le": PCMCodec.PCM_F64LE,
    "s16le": PCMCodec.PCM_S16LE,
    "s24le": PCMCodec.PCM_S24LE,
    "s32le": PCMCodec.PCM_S32LE,
    "f32le": PCMCodec.PCM_F32LE,
    "f64le": PCMCodec.PCM_F64LE,
}

OUTPUT_DIR = Path("examples/outputs")


def parse_args(args: list[str] | None = None) -> argparse.Namespace:
    """Parse command-line arguments for WAV encoding.

    Args:
        args: List of command-line argument strings, or None to use sys.argv.

    Returns:
        argparse.Namespace: Parsed command-line arguments.
    """
    parser = argparse.ArgumentParser(
        description="Encode an audio file to WAV with custom parameters.",
        formatter_class=argparse.ArgumentDefaultsHelpFormatter,
    )
    parser.add_argument(
        "input_file",
        nargs="?",
        type=Path,
        default=Path("samples/sample.mp3"),
        help="Path to input audio file",
    )
    parser.add_argument(
        "-c",
        "--codec",
        type=str.lower,
        choices=list(WAV_SUPPORTED_CODECS.keys()),
        default="pcm_s16le",
        help="PCM codec for WAV encoding",
    )
    parser.add_argument(
        "--overwrite",
        action=argparse.BooleanOptionalAction,
        default=True,
        help="Overwrite output file if it already exists",
    )
    return parser.parse_args(args)


def main() -> None:
    """Run WAV encoding with command-line arguments."""
    args = parse_args()
    input_path: Path = args.input_file

    if not input_path.exists():
        print(f"Error: Input file not found at '{input_path}'", file=sys.stderr)
        sys.exit(1)

    codec_enum = WAV_SUPPORTED_CODECS[args.codec]
    codec_name = "wav"
    output_filename = f"{input_path.stem}_{codec_name}_{codec_enum.value}.wav"
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    output_path = OUTPUT_DIR / output_filename

    print(f"Input file:  {input_path}")
    print(f"Output file: {output_path}")
    print(f"Format:      {codec_name.upper()}")
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

    print("\nEncoding to WAV...")
    encoder = WAVEncoder(codec=codec_enum)

    try:
        encoder(pcm, output_path, overwrite=args.overwrite)
        file_size_kb = output_path.stat().st_size / 1024
        print(f"Encoding successful: {output_path} ({file_size_kb:.1f} KB)")
    except PyFFmpegAudioIOError as e:
        print(f"Error encoding audio: {e}", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()
