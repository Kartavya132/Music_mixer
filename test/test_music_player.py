import csv
import sys
from pathlib import Path
from types import SimpleNamespace

from func.function import add_music_to_library, admin, music_player


def test_add_music_to_library_updates_csv(tmp_path):
    sample_dir = tmp_path / "music"
    sample_dir.mkdir()
    csv_path = tmp_path / "music.csv"

    source_file = tmp_path / "source_track.mp3"
    source_file.write_text("sample mp3 content", encoding="utf-8")

    rows = add_music_to_library(source_file, music_dir=sample_dir, csv_path=csv_path)

    assert (sample_dir / "track_1.wav").exists()
    assert not (sample_dir / "source_track.mp3").exists()
    assert len(rows) == 1
    assert rows[0]["music"] == "track_1.wav"
    assert rows[0]["location"] == str((sample_dir / "track_1.wav").resolve())


def test_sync_music_csv_replaces_placeholder_files(tmp_path):
    sample_dir = tmp_path / "music"
    sample_dir.mkdir()
    csv_path = tmp_path / "music.csv"

    for name in ["sample_track_1.mp3", "sample_track_2.mp3"]:
        (sample_dir / name).write_text(
            "This is a placeholder sample MP3 file for testing.\r\n",
            encoding="utf-8",
        )

    rows = add_music_to_library(
        sample_dir / "sample_track_1.mp3",
        music_dir=sample_dir,
        csv_path=csv_path,
    )

    assert len(rows) == 2
    assert (sample_dir / "track_1.wav").exists()
    assert (sample_dir / "track_2.wav").exists()
    assert not (sample_dir / "sample_track_1.mp3").exists()
    assert not (sample_dir / "sample_track_2.mp3").exists()


def test_music_player_with_sample_mp3_files(tmp_path, monkeypatch):
    sample_dir = tmp_path / "music"
    sample_dir.mkdir()

    sample_files = [
        sample_dir / "track1.mp3",
        sample_dir / "track2.mp3",
        sample_dir / "track3.mp3",
    ]

    for sample in sample_files:
        sample.write_text("sample mp3 content", encoding="utf-8")

    csv_path = tmp_path / "music.csv"

    class FakeMediaPlayer:
        def __init__(self):
            self.paths = []
            self._playing = True

        def set_mrl(self, file_path):
            self.paths.append(file_path)
            self._playing = True

        def play(self):
            self._playing = True

        def is_playing(self):
            if self._playing:
                self._playing = False
                return True
            return False

    fake_player = FakeMediaPlayer()

    monkeypatch.setitem(
        sys.modules,
        "vlc",
        SimpleNamespace(
            Instance=lambda: SimpleNamespace(media_player_new=lambda: fake_player)
        ),
    )

    music_player(sample_dir, max_passes=1, csv_path=csv_path)

    assert len(fake_player.paths) == len(sample_files)
    assert all(path.endswith(".wav") for path in fake_player.paths)

    with csv_path.open("r", encoding="utf-8", newline="") as csv_file:
        rows = list(csv.DictReader(csv_file))

    assert rows
    assert rows[0]["music"] == "track_1.wav"
    assert "Enjoy track 1" in rows[0]["intro"]
    assert "size" in rows[0]
    assert "location" in rows[0]


def test_admin_can_add_and_delete_song(tmp_path, monkeypatch):
    sample_dir = tmp_path / "music"
    sample_dir.mkdir()
    csv_path = tmp_path / "music.csv"

    source_file = tmp_path / "source_track.mp3"
    source_file.write_text("sample mp3 content", encoding="utf-8")

    responses = iter(["1", str(source_file), "4"])

    def fake_input(prompt=""):
        return next(responses)

    monkeypatch.setattr("builtins.input", fake_input)

    admin(music_dir=sample_dir, csv_path=csv_path)

    assert (sample_dir / "track_1.wav").exists()

    with csv_path.open("r", encoding="utf-8", newline="") as csv_file:
        rows = list(csv.DictReader(csv_file))

    assert len(rows) == 1
    assert rows[0]["music"] == "track_1.wav"
    assert rows[0]["location"] == str((sample_dir / "track_1.wav").resolve())

    responses = iter(["2", "track_1.wav", "4"])
    monkeypatch.setattr("builtins.input", fake_input)

    admin(music_dir=sample_dir, csv_path=csv_path)

    assert not (sample_dir / "track_1.wav").exists()

    with csv_path.open("r", encoding="utf-8", newline="") as csv_file:
        rows = list(csv.DictReader(csv_file))

    assert rows == []
