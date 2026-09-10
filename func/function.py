import csv
import random
import shutil
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
    music_files = sorted(
        music_file for music_file in music_dir.glob("*.mp3") if music_file.is_file()
    )

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

        source_path = Path(source_file).expanduser()
        if not source_path.exists() or not source_path.is_file():
            raise FileNotFoundError(f"Source file not found: {source_path}")

        if source_path.suffix.lower() != ".mp3":
            raise ValueError("Only .mp3 files can be added.")

        destination_path = music_dir / source_path.name
        shutil.copy2(source_path, destination_path)
        print(f"Added {destination_path.name} to {music_dir}")
        sync_music_csv(music_dir=music_dir, csv_path=csv_path)

    def delete_song():
        rows = sync_music_csv(music_dir=music_dir, csv_path=csv_path)
        if not rows:
            print("No songs available to delete.")
            return

        print("Available songs:")
        for row in rows:
            print(f"- {row['music']} (location: {row['location']})")

        song_name = input("Enter the song name to delete: ").strip()
        target_path = music_dir / song_name

        if not target_path.exists():
            raise FileNotFoundError(f"Song not found in the music folder: {song_name}")

        target_path.unlink()
        sync_music_csv(music_dir=music_dir, csv_path=csv_path)
        print(f"Deleted {song_name} from {music_dir} and updated CSV.")

    print("\nMusic Admin Panel")
    print("1. Add a new song")
    print("2. Delete a song")
    print("3. List songs")
    print("4. Exit")

    while True:
        choice = input("Choose an option: ").strip()

        if choice == "1":
            try:
                add_song()
            except Exception as exc:
                print(f"Error: {exc}")
        elif choice == "2":
            try:
                delete_song()
            except Exception as exc:
                print(f"Error: {exc}")
        elif choice == "3":
            rows = sync_music_csv(music_dir=music_dir, csv_path=csv_path)
            if not rows:
                print("No songs found.")
            else:
                print("Songs in the library:")
                for row in rows:
                    print(
                        f"- {row['music']} | size: {row['size']} | location: {row['location']}"
                    )
        elif choice == "4":
            print("Exiting admin panel.")
            break
        else:
            print("Invalid option. Please choose 1, 2, 3, or 4.")

    return sync_music_csv(music_dir=music_dir, csv_path=csv_path)


def music_player(music_dir=None, max_passes=None, csv_path=None):
    if music_dir is None:
        music_dir = (Path(__file__).resolve().parent.parent / "music").resolve()
    else:
        music_dir = Path(music_dir).resolve()

    if csv_path is None:
        csv_path = (Path(__file__).resolve().parent / "music.csv").resolve()
    else:
        csv_path = Path(csv_path).resolve()

    sync_music_csv(music_dir=music_dir, csv_path=csv_path)

    try:
        from playsound import playsound
    except ImportError as exc:
        raise RuntimeError(
            "playsound is required to play the music. Install it with: pip install playsound"
        ) from exc

    passes_played = 0

    try:
        while True:
            playlist = sorted(music_dir.glob("*.mp3"))
            if not playlist:
                raise FileNotFoundError(f"No .mp3 files found in: {music_dir}")

            random.shuffle(playlist)

            for music_file in playlist:
                print(f"Now playing: {music_file.name}")
                playsound(str(music_file), block=True)

            passes_played += 1
            print("Playlist finished. Shuffling and replaying...")

            if max_passes is not None and passes_played >= max_passes:
                break
    except KeyboardInterrupt:
        print("\nMusic player stopped by user.")


if __name__ == "__main__":
    print('Oops!! you came in wrong file.\nGo to "main.py" and enjoy the music\n')
