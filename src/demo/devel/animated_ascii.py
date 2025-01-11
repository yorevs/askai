import shutil
import signal
import sys
import threading
import time
from os.path import dirname, expandvars
import os
from pathlib import Path
from threading import Thread
from typing import Optional

from hspylib.core.exception.exceptions import InvalidArgumentError
from hspylib.core.metaclass.classpath import AnyPath
from rich.console import Console
from rich.text import Text
import pause
from PIL import Image
from PIL.Image import Resampling
from clitt.core.term.cursor import cursor
from hspylib.modules.application.exit_status import ExitStatus
from clitt.core.term.terminal import terminal, Terminal

from askai.core.component.audio_player import player

PALETTES = {
    1: " .:-=+*#%@",
    2: " ▁▂▃▄▅▆▇█▊",
    3: " ░▒▓█▓▒░▒▓",
}

FPS: int = 10

DEFAULT_PALETTE = PALETTES[1]

VIDEO_DIR: Path = Path(expandvars("${HOME}/Movies"))
if not VIDEO_DIR.exists():
    VIDEO_DIR.mkdir(parents=True, exist_ok=True)

DATA_PATH: Path = Path(os.path.join(dirname(__file__), 'AscVideos'))
if not DATA_PATH.exists():
    DATA_PATH.mkdir(parents=True, exist_ok=True)


def image_to_ascii(
    frame_path: str,
    width: int,
    palette: str,
    reverse: bool
) -> str:
    """Converts an image frame to an ASCII art representation.
    :param frame_path: Path to the image file to be converted.
    :param width: Width of the output ASCII art in characters.
    :param palette: String of characters to use for ASCII art shading.
    :param reverse: Whether to reverse the shading palette.
    :return: A string containing the ASCII art representation of the image.
    """
    num_chars = len(palette if not reverse else palette[::-1])
    img: Image = Image.open(frame_path).convert("L")
    aspect_ratio = img.height / img.width
    new_height = int(width * aspect_ratio * 0.4)
    img = img.resize((width, new_height), resample=Resampling.BILINEAR)
    pixels = list(img.getdata())
    ascii_str = "".join(palette[min(pixel * num_chars // 256, num_chars - 1)] for pixel in pixels)
    ascii_lines = [ascii_str[i:i + width] for i in range(0, len(ascii_str), width)]

    return "\n".join(ascii_lines)


def get_frames(
    frames_path: Path,
    width: int = 80,
    palette: str = DEFAULT_PALETTE,
    reverse: bool = True
) -> list[str]:
    """Converts all frame files in the specified directory to ASCII format.
    :param frames_path: Path to the directory containing frame files.
    :param width: Width of the output ASCII art in characters. Defaults to 80.
    :param palette: String of characters to use for ASCII art shading.
    :param reverse: Whether to reverse the shading palette. Defaults to True.
    :return: List of ASCII representations of the frames.
    """
    ascii_frames: list[str] = []
    for frame_file in sorted(os.listdir(frames_path)):
        frame_path: str = os.path.join(frames_path, frame_file)
        ascii_frame = image_to_ascii(frame_path, width, palette, reverse)
        ascii_frames.append(ascii_frame)

    return ascii_frames


def extract_audio_and_video_frames(video_path: Path) -> tuple[Optional[Path], Path]:
    """Extracts audio and video frames from the given video path.
    :param video_path: Path to the video file to extract audio and frames from.
    :return: A tuple containing the path to the extracted audio and a list of paths to the video frames, or None if
             the extraction fails.
    """
    assert video_path.exists(), f"Video path does not exist: {video_path}"
    video_name, _ = os.path.splitext(os.path.basename(video_path))
    frame_dir: Path = Path(os.path.join(DATA_PATH, video_name, 'frames'))
    audio_dir: Path = Path(os.path.join(DATA_PATH, video_name, 'audio'))
    audio_path: Path = Path(os.path.join(audio_dir, "audio.mp3"))

    # If output directory doesn't exist, perform extraction
    if not frame_dir.exists():
        frame_dir.mkdir(parents=True, exist_ok=True)
        audio_dir.mkdir(parents=True, exist_ok=True)

        # Extract frames
        frame_command = f'ffmpeg -i "{video_path}" -vf "fps={FPS}" "{frame_dir}/frame%04d.png"'
        _, _, exit_code = terminal.shell_exec(frame_command, shell=True)
        if exit_code != ExitStatus.SUCCESS:
            raise InvalidArgumentError(f"Failed to extract video frames from: {video_path}")

        # Extract audio
        audio_command = f'ffmpeg -i "{video_path}" -q:a 0 -map a "{audio_path}"'
        _, _, exit_code = terminal.shell_exec(audio_command, shell=True)
        if exit_code != ExitStatus.SUCCESS:
            raise InvalidArgumentError(f"Failed to extract video frames from: {audio_path}")

    return audio_path if audio_path.exists() else None, frame_dir


def play_ascii_frames(ascii_frames: list[str], fps: int) -> None:
    """Plays a sequence of ASCII art frames in the terminal with a specified delay.
    :param ascii_frames: List of ASCII art frames to display.
    :param fps: Frames per second to control the delay between frames.
    :return: None
    :raises OSError: If unable to get terminal size.
    """
    delay_ms: int = int(1000 / fps)
    for frame in ascii_frames:
        start_time = time.perf_counter()  # Record the start time
        print_ascii_image(frame)
        end_time = time.perf_counter()  # Record the end time
        render_time: int = int((end_time - start_time) * 1000)
        pause.milliseconds(delay_ms - render_time)


def print_ascii_image(image: str) -> None:
    """Prints an ASCII image to the console, centering each line and clearing the current line after printing.
    :param image: The ASCII image as a string, with lines separated by newline characters.
    :return: None
    :raises ValueError: If the terminal size cannot be determined or if the image is not a valid string.
    """
    console = Console()
    cursor.write("%HOM%")
    cols, _ = shutil.get_terminal_size()
    for line in image.splitlines()[:cols]:
        console.print(Text(line, justify="center"), end='')
        cursor.write(f"%EL0%%EOL%")


def play_video(ascii_frames: list[str], fps: int) -> Thread:
    """Plays a list of ASCII art frames as a video in a separate thread.
    :param ascii_frames: List of ASCII art frames to display.
    :param fps: Frames per second at which to display the frames.
    :return: Thread object running the video playback.
    """
    thread = threading.Thread(target=play_ascii_frames, args=(ascii_frames, fps))
    thread.daemon = True
    thread.start()
    return thread


def play_audio(audio_path: AnyPath) -> Optional[Thread]:
    """Plays an audio file in a separate thread.
    :param audio_path: Path to the audio file to be played.
    :return: The thread running the audio playback.
    """
    if os.path.exists(str(audio_path)):
        thread = threading.Thread(target=player.play_audio_file, args=(str(audio_path),))
        thread.daemon = True
        thread.start()
        return thread
    return None


def setup_terminal() -> None:
    """Setup the terminal screen to render the video."""
    Terminal.alternate_screen(True)
    Terminal.clear()
    Terminal.set_show_cursor(False)
    signal.signal(signal.SIGINT, cleanup)
    signal.signal(signal.SIGTERM, cleanup)
    signal.signal(signal.SIGABRT, cleanup)


def cleanup(*args) -> None:
    """Provide a cleanup for graceful exit."""
    try:
        Terminal.clear()
        Terminal.alternate_screen(False)
        Terminal.clear()
        Terminal.set_show_cursor(True)
        sys.exit()
    except SystemExit:
        exit()


def play(video_name: str, width: int = 80) -> None:
    """Plays a video in ASCII format with synchronized audio.
    :param video_name: The name of the video file to play.
    :param width: TODO
    """
    # cols, rows = shutil.get_terminal_size()
    # print(cols, rows, cols / rows)
    # exit()
    video_path: Path = Path(
        os.path.join(VIDEO_DIR, video_name)
        if not os.path.exists(expandvars(video_name)) else expandvars(video_name)
    )
    audio_path, frames_path = extract_audio_and_video_frames(video_path)
    ascii_video = get_frames(frames_path, width, PALETTES[1], True)
    setup_terminal()
    thv = play_video(ascii_video, FPS)
    if audio_path is not None and audio_path.exists():
        tha = play_audio(audio_path)
        tha.join()
    thv.join()
    cleanup()


if __name__ == '__main__':
    play("${DESKTOP}/robot.mp4", 50)
    # asc_img = image_to_ascii(expandvars("${DESKTOP}/robot.png"), 74, DEFAULT_PALETTE, True)
    # print_ascii_image(asc_img)
