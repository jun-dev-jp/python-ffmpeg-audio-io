"""Example script demonstrating AAC encoding with command-line arguments."""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

from python_ffmpeg_audio_io.decoder import decode
from python_ffmpeg_audio_io.encoder.aac import (
    AACEncoder,
    AACEncoderBitrate,
    AACEncoderMode,
    AACEncoderQualityLevel,
)
from python_ffmpeg_audio_io.exceptions import PyFFmpegAudioIOError
from python_ffmpeg_audio_io.pcm import PCMCodec

OUTPUT_DIR = Path("examples/outputs")


def parse_args(args: list[str] | None = None) -> argparse.Namespace:
    """Parse command-line arguments for AAC encoding.

    Args:
        args: List of command-line argument strings, or None to use sys.argv.

    Returns:
        argparse.Namespace: Parsed command-line arguments.
    """
    parser = argparse.ArgumentParser(
        description="Encode an audio file to AAC with custom parameters.",
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
        "-m",
        "--mode",
        type=str.lower,
        choices=[m.name.lower() for m in AACEncoderMode],
        default=AACEncoderMode.CBR.name.lower(),
        help="Encoding mode (cbr, abr, vbr)",
    )
    parser.add_argument(
        "-b",
        "--bitrate",
        choices=[b.value for b in AACEncoderBitrate],
        default=AACEncoderBitrate.Kbps_192.value,
        help="Bitrate for CBR and ABR modes",
    )
    parser.add_argument(
        "-q",
        "--quality",
        type=int,
        choices=[q.value for q in AACEncoderQualityLevel],
        default=AACEncoderQualityLevel.Quality_5.value,
        help="Quality level for VBR mode (0=worst, 5=best)",
    )
    parser.add_argument(
        "--overwrite",
        action=argparse.BooleanOptionalAction,
        default=True,
        help="Overwrite output file if it already exists",
    )
    return parser.parse_args(args)


def main() -> None:
    """Run AAC encoding with command-line arguments."""
    args = parse_args()
    input_path: Path = args.input_file

    if not input_path.exists():
        print(f"Error: Input file not found at '{input_path}'", file=sys.stderr)
        sys.exit(1)

    mode_enum = AACEncoderMode[args.mode.upper()]
    bitrate_enum = AACEncoderBitrate(args.bitrate)
    quality_enum = AACEncoderQualityLevel(args.quality)

    # Determine parameter string for descriptive output filename
    if mode_enum == AACEncoderMode.VBR:
        param_str = f"vbr_q{quality_enum.value}"
    else:
        param_str = f"{mode_enum.value.lower()}_{bitrate_enum.value}"

    output_filename = f"{input_path.stem}_{param_str}.m4a"
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    output_path = OUTPUT_DIR / output_filename

    print(f"Input file:  {input_path}")
    print(f"Output file: {output_path}")
    print("Codec:       AAC")
    print(f"Mode:        {mode_enum.value}")
    if mode_enum == AACEncoderMode.VBR:
        print(f"Quality:     {quality_enum.value} (0=worst, 5=best)")
    else:
        print(f"Bitrate:     {bitrate_enum.value}")

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

    print("\nEncoding to AAC...")
    encoder = AACEncoder(
        bitrate=bitrate_enum,
        mode=mode_enum,
        quality=quality_enum,
    )

    try:
        encoder(pcm, output_path, overwrite=args.overwrite)
        file_size_kb = output_path.stat().st_size / 1024
        print(f"Encoding successful: {output_path} ({file_size_kb:.1f} KB)")
    except PyFFmpegAudioIOError as e:
        print(f"Error encoding audio: {e}", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()
