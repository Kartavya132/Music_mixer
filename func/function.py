import csv
import math
import random
import shutil
import struct
import sys
import time
import wave
from datetime import datetime
from pathlib import Path

MAX_VOLUME = 150
_active_media_player = None


def _project_root():
    if getattr(sys, "frozen", False):
        return Path(sys.executable).resolve().parent
    return Path(__file__).resolve().parent.parent


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


def _has_audio_data(music_file):
    try:
        return music_file.stat().st_size > 0
    except OSError:
        return False


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
    """Keep all music files intact.

    Invalid placeholder files are left alone and simply ignored when building the
    CSV. We never rename or delete a user's actual music track.
    """
    if not music_dir.exists():
        return
    return


def _normalize_music_file_names(music_dir):
    """Leave file names as-is to preserve the user's music library."""
    if not music_dir.exists():
        return
    return


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
            f"Status: {row['status']} | "
            f"Location: {row['location']}"
        )


def add_music_to_library(source_file, music_dir=None, csv_path=None):
    if music_dir is None:
        music_dir = (_project_root() / "music").resolve()
    else:
        music_dir = Path(music_dir).resolve()

    if csv_path is None:
        csv_path = (_project_root() / "func" / "music.csv").resolve()
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
        music_dir = (_project_root() / "music").resolve()
    else:
        music_dir = Path(music_dir).resolve()

    if csv_path is None:
        csv_path = (_project_root() / "func" / "music.csv").resolve()
    else:
        csv_path = Path(csv_path).resolve()

    if not music_dir.exists():
        raise FileNotFoundError(f"Music folder not found: {music_dir}")

    music_dir.mkdir(parents=True, exist_ok=True)
    _repair_placeholder_music_files(music_dir)

    music_files = []
    for pattern in ("*.mp3", "*.wav"):
        for music_file in music_dir.glob(pattern):
            if not music_file.is_file():
                continue
            music_files.append(music_file)
    music_files = sorted(music_files, key=lambda item: item.name.lower())

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
                "status": "Ready" if _has_audio_data(music_file) else "Empty file",
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
        "status",
        "location",
    ]
    with csv_path.open("w", newline="", encoding="utf-8") as csv_file:
        writer = csv.DictWriter(csv_file, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)

    return rows


def admin(music_dir=None, csv_path=None):
    if music_dir is None:
        music_dir = (_project_root() / "music").resolve()
    else:
        music_dir = Path(music_dir).resolve()

    if csv_path is None:
        csv_path = (_project_root() / "func" / "music.csv").resolve()
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


def _get_music_playlist(music_dir):
    playlist = []
    for pattern in ("*.mp3", "*.wav"):
        playlist.extend(
            music_file
            for music_file in music_dir.glob(pattern)
            if music_file.is_file() and _has_audio_data(music_file)
        )

    unique_playlist = {path.resolve(): path for path in playlist}
    return sorted(unique_playlist.values(), key=lambda item: item.name.lower())


def _wait_for_media_player_to_finish(media_player, vlc_module=None):
    if vlc_module is not None and hasattr(media_player, "get_state"):
        state_enum = getattr(vlc_module, "State", None)
        if state_enum is not None:
            started = False
            while True:
                try:
                    state = media_player.get_state()
                except Exception:
                    break

                if state == getattr(state_enum, "Playing", None):
                    started = True

                if (
                    state
                    in (
                        getattr(state_enum, "Ended", None),
                        getattr(state_enum, "Stopped", None),
                        getattr(state_enum, "Error", None),
                    )
                    and started
                ):
                    return

                time.sleep(0.05)

    # VLC can briefly report false while it is opening a newly selected file.
    started = False
    startup_deadline = time.monotonic() + 5
    while not started and time.monotonic() < startup_deadline:
        if media_player.is_playing():
            started = True
            break
        time.sleep(0.05)

    while started and media_player.is_playing():
        time.sleep(0.05)


def _ramp_volume_to_target(media_player, target_volume, step=10, delay=0.05):
    if not hasattr(media_player, "audio_set_volume"):
        return

    target_volume = max(0, min(MAX_VOLUME, int(target_volume)))
    current_volume = 0

    while current_volume < target_volume:
        current_volume = min(current_volume + step, target_volume)
        media_player.audio_set_volume(current_volume)
        time.sleep(delay)

    media_player.audio_set_volume(target_volume)


def _release_vlc_player(media_player, instance):
    if media_player is not None:
        try:
            media_player.stop()
        except Exception:
            pass
        try:
            media_player.release()
        except Exception:
            pass

    if instance is not None:
        try:
            instance.release()
        except Exception:
            pass


def _play_music_file_with_vlc(music_file, volume=MAX_VOLUME):
    global _active_media_player

    try:
        import vlc
    except ImportError as exc:
        raise RuntimeError(
            "python-vlc is required to play the music. Install VLC and the Python package with: py -m pip install python-vlc"
        ) from exc

    instance = vlc.Instance()
    media_player = instance.media_player_new()
    _active_media_player = media_player

    try:
        if hasattr(instance, "media_new") and hasattr(media_player, "set_media"):
            media = instance.media_new(str(music_file))
            media_player.set_media(media)
        else:
            media_player.set_mrl(str(music_file))

        if hasattr(media_player, "audio_set_volume"):
            media_player.audio_set_volume(0)

        media_player.play()
        _ramp_volume_to_target(media_player, volume)
        _wait_for_media_player_to_finish(media_player, vlc_module=vlc)
    finally:
        _release_vlc_player(media_player, instance)
        _active_media_player = None


def stop_music_player():
    """Stop the currently playing track so the process can exit cleanly."""
    global _active_media_player

    if _active_media_player is not None:
        try:
            _active_media_player.stop()
        except Exception:
            pass


def play_randomized_music_from_folder(
    music_dir=None, max_passes=None, csv_path=None, volume=MAX_VOLUME
):
    if music_dir is None:
        music_dir = (_project_root() / "music").resolve()
    else:
        music_dir = Path(music_dir).resolve()

    if csv_path is None:
        csv_path = (_project_root() / "func" / "music.csv").resolve()
    else:
        csv_path = Path(csv_path).resolve()

    rows = sync_music_csv(music_dir=music_dir, csv_path=csv_path)

    if not rows:
        raise FileNotFoundError(f"No playable music files found in: {music_dir}")

    _print_header("NOW PLAYING")
    playable_count = len(_get_music_playlist(music_dir))
    print(f"Library: {len(rows)} tracks | Ready to play: {playable_count}")
    print(f"Music folder: {music_dir}")
    print(f"Playback volume: {MAX_VOLUME}/{MAX_VOLUME} (maximum)")
    print("The playlist will shuffle and loop automatically. Press Ctrl+C to stop.")

    passes_played = 0

    try:
        while True:
            playlist = _get_music_playlist(music_dir)

            if not playlist:
                raise FileNotFoundError(
                    f"No playable music files found in: {music_dir}"
                )

            random.shuffle(playlist)

            for index, music_file in enumerate(playlist, start=1):
                print(f"\n[{index}/{len(playlist)}] Now playing: {music_file.name}")
                _play_music_file_with_vlc(music_file, volume=volume)

            passes_played += 1
            print("\nPlaylist finished. Shuffling and replaying...")

            if max_passes is not None and passes_played >= max_passes:
                break
    except KeyboardInterrupt:
        stop_music_player()
        print("\nMusic player stopped by user.")


def music_player(music_dir=None, max_passes=None, csv_path=None, volume=MAX_VOLUME):
    play_randomized_music_from_folder(
        music_dir=music_dir,
        max_passes=max_passes,
        csv_path=csv_path,
        volume=volume,
    )


if __name__ == "__main__":
    print('Oops!! you came in wrong file.\nGo to "main.py" and enjoy the music\n')
