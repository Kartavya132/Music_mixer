import csv
import sys
from pathlib import Path
from types import SimpleNamespace

from func.function import admin, music_player


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

    played = []
    csv_path = tmp_path / "music.csv"

    def fake_playsound(file_path, block=True):
        played.append((file_path, block))

    monkeypatch.setitem(
        sys.modules,
        "playsound",
        SimpleNamespace(playsound=fake_playsound),
    )

    music_player(sample_dir, max_passes=1, csv_path=csv_path)

    assert len(played) == len(sample_files)
    assert all(path.endswith(".mp3") for path, _ in played)

    with csv_path.open("r", encoding="utf-8", newline="") as csv_file:
        rows = list(csv.DictReader(csv_file))

    assert rows
    assert rows[0]["music"] == "track1.mp3"
    assert "Enjoy track1" in rows[0]["intro"]
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

    assert (sample_dir / "source_track.mp3").exists()

    with csv_path.open("r", encoding="utf-8", newline="") as csv_file:
        rows = list(csv.DictReader(csv_file))

    assert len(rows) == 1
    assert rows[0]["music"] == "source_track.mp3"
    assert rows[0]["location"] == str((sample_dir / "source_track.mp3").resolve())

    responses = iter(["2", "source_track.mp3", "4"])
    monkeypatch.setattr("builtins.input", fake_input)

    admin(music_dir=sample_dir, csv_path=csv_path)

    assert not (sample_dir / "source_track.mp3").exists()

    with csv_path.open("r", encoding="utf-8", newline="") as csv_file:
        rows = list(csv.DictReader(csv_file))

    assert rows == []
