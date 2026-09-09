import random
import time
from pathlib import Path

import pandas as pd


def admin():
    pass


def _show_notification(message):
    try:
        import tkinter as tk
        from tkinter import messagebox

        root = tk.Tk()
        root.withdraw()
        messagebox.showinfo("Music Player", message)
        root.destroy()
    except Exception:
        print(f"[Music Player Notification] {message}")


def music_player(music_dir=None):
    if music_dir is None:
        music_dir = (Path(__file__).resolve().parent.parent / "music").resolve()
    else:
        music_dir = Path(music_dir).resolve()

    if not music_dir.exists():
        raise FileNotFoundError(f"Music folder not found: {music_dir}")

    playlist = sorted(music_dir.glob("*.mp3"))
    if not playlist:
        raise FileNotFoundError(f"No .mp3 files found in: {music_dir}")

    try:
        pygame = __import__("pygame")
    except ImportError as exc:
        raise RuntimeError(
            "pygame is required to play the music. Install it with: pip install pygame"
        ) from exc

    try:
        pygame.init()
        pygame.mixer.init()
    except Exception as exc:
        raise RuntimeError(
            "Could not initialize the pygame mixer. Check that audio devices are available."
        ) from exc

    try:
        while True:
            playlist = sorted(music_dir.glob("*.mp3"))
            if not playlist:
                raise FileNotFoundError(f"No .mp3 files found in: {music_dir}")

            random.shuffle(playlist)

            for music_file in playlist:
                print(f"Now playing: {music_file.name}")
                pygame.mixer.music.load(str(music_file))
                pygame.mixer.music.play()

                while pygame.mixer.music.get_busy():
                    time.sleep(0.5)

            _show_notification(
                "All files in the music folder have been played. Shuffling the playlist and starting again."
            )
    except KeyboardInterrupt:
        pygame.mixer.music.stop()
        print("\nMusic player stopped by user.")


if __name__ == "__main__":
    print('Oops!! you came in wrong file.\nGo to "main.py" and enjoy the music\n')
