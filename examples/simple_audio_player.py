"""Example: Stream audio playback with SoundDevice."""

from __future__ import annotations

import argparse
import sys
from pathlib import Path
from threading import Condition, Thread

import sounddevice as sd  # type: ignore[reportMissingTypeStubs]

from python_ffmpeg_audio_io import AudioStreamReader, PCMCodec
from python_ffmpeg_audio_io.exceptions import PyFFmpegAudioIOError


class SimpleAudioPlayer:
    """Control streamed audio playback from the console."""

    def __init__(self, input_file: Path, chunk_frames: int = 1024) -> None:
        """Initialize the player.

        Args:
            input_file: Path to the audio file to play.
            chunk_frames: Number of PCM frames to read and play at a time.
        """
        self._input_file = input_file
        self._chunk_frames = chunk_frames
        self._condition = Condition()
        self._playback_thread: Thread | None = None
        self._playing = False
        self._paused = False
        self._shutdown = False
        self._finished = False
        self._playback_error: Exception | None = None

    def play(self) -> bool:
        """Start or resume playback.

        Returns:
            True if playback was started or resumed, or False if already playing.
        """
        playback_thread = self._playback_thread
        if playback_thread is not None:
            with self._condition:
                if playback_thread.is_alive() and not self._finished:
                    if self._playing:
                        return False
                    self._playing = True
                    self._condition.notify_all()
                    return True
            playback_thread.join()

        with self._condition:
            self._playing = True
            self._paused = False
            self._shutdown = False
            self._finished = False
            self._playback_error = None
            playback_thread = Thread(target=self._playback_worker)
            self._playback_thread = playback_thread
            playback_thread.start()
        return True

    def stop(self) -> bool:
        """Pause playback at the current chunk position.

        Returns:
            True if playback was active and has been paused.
        """
        with self._condition:
            playback_thread = self._playback_thread
            if (
                playback_thread is None
                or not playback_thread.is_alive()
                or self._finished
                or not self._playing
            ):
                return False
            self._playing = False
            self._condition.notify_all()
            self._condition.wait_for(lambda: self._paused or self._finished)
        return True

    def run(self) -> int:
        """Display and handle playback commands until the user exits.

        Returns:
            Process exit status.
        """
        print(f"Audio file: {self._input_file}")
        print("Commands:")
        print("  p / play  - Start or resume playback")
        print("  s / stop  - Pause playback at the current position")
        print("  q / quit  - Exit")

        try:
            while True:
                try:
                    command = input("Command> ").strip().lower()
                except EOFError:
                    command = "q"

                if command in {"p", "play"}:
                    if self.play():
                        print("Playing or resuming...")
                    else:
                        print("Playback is already running.")
                elif command in {"s", "stop"}:
                    if self.stop():
                        print("Playback paused.")
                    else:
                        print("Playback is not running.")
                elif command in {"q", "quit", "exit"}:
                    break
                else:
                    print("Unknown command. Enter p, s, or q.")
        except KeyboardInterrupt:
            print()
        finally:
            self._shutdown_playback()

        return 1 if self._playback_error is not None else 0

    def _playback_worker(self) -> None:
        """Run playback and report library or audio-device errors."""
        try:
            self._playback_loop()
        except (PyFFmpegAudioIOError, sd.PortAudioError) as error:
            with self._condition:
                self._playback_error = error
            print(f"\nError playing audio: {error}", file=sys.stderr)
        finally:
            with self._condition:
                self._playing = False
                self._paused = False
                self._finished = True
                self._condition.notify_all()

    def _playback_loop(self) -> None:
        """Stream decoded chunks to the default audio output device."""
        with AudioStreamReader(
            self._input_file,
            pcm_codec=PCMCodec.PCM_S16LE,
            chunk_frames=self._chunk_frames,
        ) as reader:
            with sd.OutputStream(
                samplerate=reader.sample_rate.value,
                channels=reader.channels.value,
                dtype="int16",
            ) as output_stream:
                while self._wait_until_playing():
                    chunk = reader.read()
                    if chunk is None or not self._wait_until_playing():
                        return
                    output_stream.write(  # type: ignore[reportUnknownMemberType]
                        chunk.as_numpy()
                    )

    def _wait_until_playing(self) -> bool:
        """Wait until playback resumes or the player is shutting down."""
        with self._condition:
            while not self._playing and not self._shutdown:
                self._paused = True
                self._condition.notify_all()
                self._condition.wait()

            self._paused = False
            self._condition.notify_all()
            return not self._shutdown

    def _shutdown_playback(self) -> None:
        """Stop the playback thread and release its audio resources."""
        with self._condition:
            self._shutdown = True
            self._condition.notify_all()
            playback_thread = self._playback_thread

        if playback_thread is not None:
            playback_thread.join()


def parse_args(args: list[str] | None = None) -> argparse.Namespace:
    """Parse command-line arguments.

    Args:
        args: Command-line arguments, or None to use sys.argv.

    Returns:
        Parsed command-line arguments.
    """
    parser = argparse.ArgumentParser(
        description="Stream an audio file to the default output device."
    )
    parser.add_argument(
        "input_file",
        type=Path,
        help="Path to the audio file to play",
    )
    return parser.parse_args(args)


def main(args: list[str] | None = None) -> int:
    """Run the audio player.

    Args:
        args: Command-line arguments, or None to use sys.argv.

    Returns:
        Process exit status.
    """
    parsed_args = parse_args(args)
    player = SimpleAudioPlayer(parsed_args.input_file)
    return player.run()


if __name__ == "__main__":
    raise SystemExit(main())
