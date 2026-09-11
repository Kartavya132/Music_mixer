import csv
import math
import random
import shutil
import struct
import time
import wave
from datetime import datetime
from pathlib import Path


def _format_size(size_bytes):
    units = ["bytes", "KB", "MB", "GB", "TB"]
    value = float(size_bytes)

    for unit in units:
        if value < 1024 or unit == units[-1]:
            if unit == "bytes":
                return f"{int(value)} bytes"
            return f"{value:.2f} {unit}"
        value /= 1024


def _build_intro(music_file):
    title = music_file.stem.replace("_", " ").replace("-", " ")
    title = " ".join(title.split())
    if not title:
        title = music_file.name
    return f"Enjoy {title} from your music collection."


def _looks_like_real_mp3(data):
    if len(data) < 2:
        return False

    return data.startswith((b"ID3", b"\xff\xfb", b"\xff\xf3", b"\xff\xf2"))


def _create_placeholder_wav(
    target_path, duration=1.0, sample_rate=22050, frequency=440
):
    amplitude = 32767
    total_samples = int(sample_rate * duration)

    frames = []
    for index in range(total_samples):
        value = int(amplitude * math.sin(2 * math.pi * frequency * index / sample_rate))
        frames.append(struct.pack("<h", value))

    target_path.parent.mkdir(parents=True, exist_ok=True)
    with wave.open(str(target_path), "wb") as wav_file:
        wav_file.setnchannels(1)
        wav_file.setsampwidth(2)
        wav_file.setframerate(sample_rate)
        wav_file.writeframes(b"".join(frames))


def _repair_placeholder_music_files(music_dir):
    if not music_dir.exists():
        return

    for music_file in sorted(music_dir.glob("*.mp3")):
        if not music_file.is_file():
            continue

        data = music_file.read_bytes()[:16]
        if _looks_like_real_mp3(data):
            continue

        wav_path = music_dir / f"{music_file.stem}.wav"
        _create_placeholder_wav(wav_path)
        music_file.unlink()


def _normalize_music_file_names(music_dir):
    if not music_dir.exists():
        return

    music_files = []
    for pattern in ("*.mp3", "*.wav"):
        music_files.extend(
            music_file for music_file in music_dir.glob(pattern) if music_file.is_file()
        )

    music_files = sorted(music_files, key=lambda item: item.name.lower())

    for index, music_file in enumerate(music_files, start=1):
        extension = music_file.suffix.lower()
        target_name = f"track_{index}{extension}"
        target_path = music_dir / target_name

        if music_file.name == target_name:
            continue

        if target_path.exists() and target_path.resolve() != music_file.resolve():
            target_path.unlink()

        music_file.rename(target_path)


def _print_header(title):
    print("\n" + "=" * 60)
    print(title.center(60))
    print("=" * 60)


def _print_library(rows):
    if not rows:
        print("No songs found.")
        return

    print("\nMusic Library")
    for row in rows:
        print(
            f"{row['index']}. {row['music']} | "
            f"Size: {row['size']} | "
            f"Location: {row['location']}"
        )


def add_music_to_library(source_file, music_dir=None, csv_path=None):
    if music_dir is None:
        music_dir = (Path(__file__).resolve().parent.parent / "music").resolve()
    else:
        music_dir = Path(music_dir).resolve()

    if csv_path is None:
        csv_path = (Path(__file__).resolve().parent / "music.csv").resolve()
    else:
        csv_path = Path(csv_path).resolve()

    source_path = Path(source_file).expanduser()
    if not source_path.exists() or not source_path.is_file():
        raise FileNotFoundError(f"Source file not found: {source_path}")

    if source_path.suffix.lower() != ".mp3":
        raise ValueError("Only .mp3 files can be added.")

    music_dir.mkdir(parents=True, exist_ok=True)
    csv_path.parent.mkdir(parents=True, exist_ok=True)

    destination_path = music_dir / source_path.name
    if source_path.resolve() != destination_path.resolve():
        if destination_path.exists():
            destination_path.unlink()
        shutil.copy2(source_path, destination_path)

    rows = sync_music_csv(music_dir=music_dir, csv_path=csv_path)
    return rows


def sync_music_csv(music_dir=None, csv_path=None):
    if music_dir is None:
        music_dir = (Path(__file__).resolve().parent.parent / "music").resolve()
    else:
        music_dir = Path(music_dir).resolve()

    if csv_path is None:
        csv_path = (Path(__file__).resolve().parent / "music.csv").resolve()
    else:
        csv_path = Path(csv_path).resolve()

    if not music_dir.exists():
        raise FileNotFoundError(f"Music folder not found: {music_dir}")

    music_dir.mkdir(parents=True, exist_ok=True)
    _repair_placeholder_music_files(music_dir)
    _normalize_music_file_names(music_dir)

    music_files = []
    for pattern in ("*.mp3", "*.wav"):
        music_files.extend(
            music_file for music_file in music_dir.glob(pattern) if music_file.is_file()
        )
    music_files = sorted(music_files, key=lambda item: item.name)

    rows = []
    for index, music_file in enumerate(music_files, start=1):
        try:
            file_stat = music_file.stat()
            created_date = datetime.fromtimestamp(file_stat.st_ctime).strftime(
                "%Y-%m-%d"
            )
            size = _format_size(file_stat.st_size)
        except OSError:
            created_date = datetime.now().strftime("%Y-%m-%d")
            size = "0 bytes"

        rows.append(
            {
                "index": index,
                "music": music_file.name,
                "intro": _build_intro(music_file),
                "size": size,
                "created_date": created_date,
                "language": "unknown",
                "location": str(music_file.resolve()),
            }
        )

    csv_path.parent.mkdir(parents=True, exist_ok=True)

    fieldnames = [
        "index",
        "music",
        "intro",
        "size",
        "created_date",
        "language",
        "location",
    ]
    with csv_path.open("w", newline="", encoding="utf-8") as csv_file:
        writer = csv.DictWriter(csv_file, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)

    return rows


def admin(music_dir=None, csv_path=None):
    if music_dir is None:
        music_dir = (Path(__file__).resolve().parent.parent / "music").resolve()
    else:
        music_dir = Path(music_dir).resolve()

    if csv_path is None:
        csv_path = (Path(__file__).resolve().parent / "music.csv").resolve()
    else:
        csv_path = Path(csv_path).resolve()

    music_dir.mkdir(parents=True, exist_ok=True)
    csv_path.parent.mkdir(parents=True, exist_ok=True)

    def add_song():
        source_file = input("Enter the full path of the song you want to add: ").strip()
        if not source_file:
            raise ValueError("Source file path cannot be empty.")

        rows = add_music_to_library(source_file, music_dir=music_dir, csv_path=csv_path)
        added_file = music_dir / Path(source_file).expanduser().name
        print(f"\n✓ Added {added_file.name} to {music_dir}")
        return rows

    def delete_song():
        rows = sync_music_csv(music_dir=music_dir, csv_path=csv_path)
        if not rows:
            print("\nNo songs available to delete.")
            return

        _print_library(rows)
        song_name = input("\nEnter the song name to delete: ").strip()
        target_path = music_dir / song_name

        if not target_path.exists():
            raise FileNotFoundError(f"Song not found in the music folder: {song_name}")

        target_path.unlink()
        sync_music_csv(music_dir=music_dir, csv_path=csv_path)
        print(f"\n✓ Deleted {song_name} from {music_dir} and updated the CSV.")

    _print_header("MUSIC ADMIN PANEL")
    print("Manage your music library quickly and safely.")
    print("1. Add a new song")
    print("2. Delete a song")
    print("3. List songs")
    print("4. Exit")

    while True:
        choice = input("\nChoose an option: ").strip()

        if choice == "1":
            try:
                add_song()
            except Exception as exc:
                print(f"\nError: {exc}")
        elif choice == "2":
            try:
                delete_song()
            except Exception as exc:
                print(f"\nError: {exc}")
        elif choice == "3":
            rows = sync_music_csv(music_dir=music_dir, csv_path=csv_path)
            _print_library(rows)
        elif choice == "4":
            print("\nExiting admin panel. Returning to the main menu.")
            break
        else:
            print("\nInvalid option. Please choose 1, 2, 3, or 4.")

    return sync_music_csv(music_dir=music_dir, csv_path=csv_path)


def _play_music_file_with_vlc(music_file):
    try:
        import vlc
    except ImportError as exc:
        raise RuntimeError(
            "python-vlc is required to play the music. Install VLC and the Python package with: py -m pip install python-vlc"
        ) from exc

    instance = vlc.Instance()
    media_player = instance.media_player_new()
    media_player.set_mrl(str(music_file))
    media_player.play()

    while media_player.is_playing():
        time.sleep(0.05)


def music_player(music_dir=None, max_passes=None, csv_path=None):
    if music_dir is None:
        music_dir = (Path(__file__).resolve().parent.parent / "music").resolve()
    else:
        music_dir = Path(music_dir).resolve()

    if csv_path is None:
        csv_path = (Path(__file__).resolve().parent / "music.csv").resolve()
    else:
        csv_path = Path(csv_path).resolve()

    rows = sync_music_csv(music_dir=music_dir, csv_path=csv_path)

    if not rows:
        raise FileNotFoundError(f"No playable music files found in: {music_dir}")

    _print_header("NOW PLAYING")
    print(f"Loaded {len(rows)} tracks from {music_dir}")
    print("The playlist will shuffle and loop automatically.")

    passes_played = 0

    try:
        while True:
            playlist = []
            for pattern in ("*.mp3", "*.wav"):
                playlist.extend(music_dir.glob(pattern))
            playlist = sorted({path.resolve(): path for path in playlist}.values())

            if not playlist:
                raise FileNotFoundError(
                    f"No playable music files found in: {music_dir}"
                )

            random.shuffle(playlist)

            for index, music_file in enumerate(playlist, start=1):
                print(f"\n[{index}/{len(playlist)}] Now playing: {music_file.name}")
                _play_music_file_with_vlc(music_file)

            passes_played += 1
            print("\nPlaylist finished. Shuffling and replaying...")

            if max_passes is not None and passes_played >= max_passes:
                break
    except KeyboardInterrupt:
        print("\nMusic player stopped by user.")


if __name__ == "__main__":
    print('Oops!! you came in wrong file.\nGo to "main.py" and enjoy the music\n')
