"""Example script demonstrating MP3 encoding with command-line arguments."""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

from python_ffmpeg_audio_io.decoder import decode
from python_ffmpeg_audio_io.encoder.mp3 import (
    MP3Encoder,
    MP3EncoderBitrate,
    MP3EncoderMode,
    MP3EncoderQualityLevel,
)
from python_ffmpeg_audio_io.exceptions import PyFFmpegAudioIOError
from python_ffmpeg_audio_io.pcm import PCMCodec

OUTPUT_DIR = Path("examples/outputs")


def parse_args(args: list[str] | None = None) -> argparse.Namespace:
    """Parse command-line arguments for MP3 encoding.

    Args:
        args: List of command-line argument strings, or None to use sys.argv.

    Returns:
        argparse.Namespace: Parsed command-line arguments.
    """
    parser = argparse.ArgumentParser(
        description="Encode an audio file to MP3 with custom parameters.",
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
        choices=[m.name.lower() for m in MP3EncoderMode],
        default=MP3EncoderMode.CBR.name.lower(),
        help="Encoding mode (cbr, abr, vbr)",
    )
    parser.add_argument(
        "-b",
        "--bitrate",
        choices=[b.value for b in MP3EncoderBitrate],
        default=MP3EncoderBitrate.Kbps_192.value,
        help="Bitrate for CBR and ABR modes",
    )
    parser.add_argument(
        "-q",
        "--quality",
        type=int,
        choices=[q.value for q in MP3EncoderQualityLevel],
        default=MP3EncoderQualityLevel.Quality_2.value,
        help="Quality level for VBR mode (0=best, 9=worst)",
    )
    parser.add_argument(
        "--overwrite",
        action=argparse.BooleanOptionalAction,
        default=True,
        help="Overwrite output file if it already exists",
    )
    return parser.parse_args(args)


def main() -> None:
    """Run MP3 encoding with command-line arguments."""
    args = parse_args()
    input_path: Path = args.input_file

    if not input_path.exists():
        print(f"Error: Input file not found at '{input_path}'", file=sys.stderr)
        sys.exit(1)

    mode_enum = MP3EncoderMode[args.mode.upper()]
    bitrate_enum = MP3EncoderBitrate(args.bitrate)
    quality_enum = MP3EncoderQualityLevel(args.quality)

    # Determine parameter string for descriptive output filename
    if mode_enum == MP3EncoderMode.VBR:
        param_str = f"vbr_q{quality_enum.value}"
    else:
        param_str = f"{mode_enum.value.lower()}_{bitrate_enum.value}"

    output_filename = f"{input_path.stem}_{param_str}.mp3"
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    output_path = OUTPUT_DIR / output_filename

    print(f"Input file:  {input_path}")
    print(f"Output file: {output_path}")
    print("Codec:       MP3")
    print(f"Mode:        {mode_enum.value}")
    if mode_enum == MP3EncoderMode.VBR:
        print(f"Quality:     {quality_enum.value} (0=best, 9=worst)")
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

    print("\nEncoding to MP3...")
    encoder = MP3Encoder(
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
