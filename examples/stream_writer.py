"""Example script demonstrating usage of StreamWriter classes."""

from pathlib import Path

from python_ffmpeg_audio_io import (
    AudioStreamReader,
    MP3EncoderBitrate,
    MP3StreamWriter,
    PCMCodec,
    PyFFmpegAudioIOError,
)


def main() -> None:
    sample_path = Path("samples/sample.mp3")
    output_path = Path("samples/output_streamed.mp3")

    if not sample_path.exists():
        print(f"Sample file not found at {sample_path}")
        return

    print(f"Reading from: {sample_path}")
    print(f"Writing to:   {output_path}\n")

    try:
        # Stream read from source file and stream write to target file chunk-by-chunk
        with AudioStreamReader(
            sample_path,
            pcm_codec=PCMCodec.PCM_F32LE,
            chunk_frames=4096,
        ) as reader:
            with MP3StreamWriter(
                output_path,
                sample_rate=reader.sample_rate,
                channels=reader.channels,
                pcm_format=reader.pcm_format,
                bitrate=MP3EncoderBitrate.Kbps_192,
                overwrite=True,
            ) as writer:
                for chunk in reader:
                    writer.write(chunk)

                print("Streaming encode completed successfully!")
                print(f"  - Frames written: {writer.frames_written}")
                print(f"  - Bytes written:  {writer.bytes_written}")

    except PyFFmpegAudioIOError as e:
        print(f"Error during audio streaming: {e}")
    finally:
        if output_path.exists():
            output_path.unlink()

    print("\nDone!")


if __name__ == "__main__":
    main()
