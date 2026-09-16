import csv
import sys
from pathlib import Path
from types import SimpleNamespace

from func.function import (
    add_music_to_library,
    admin,
    music_player,
    play_randomized_music_from_folder,
    sync_music_csv,
)


def test_sync_music_csv_keeps_real_music_names(tmp_path):
    sample_dir = tmp_path / "music"
    sample_dir.mkdir()
    sample_file_1 = sample_dir / "sunset_dreams.mp3"
    sample_file_2 = sample_dir / "night_drive.mp3"
    sample_file_1.write_text("sample mp3 content", encoding="utf-8")
    sample_file_2.write_text("sample mp3 content", encoding="utf-8")

    csv_path = tmp_path / "music.csv"
    rows = sync_music_csv(music_dir=sample_dir, csv_path=csv_path)

    assert [row["music"] for row in rows] == [
        "night_drive.mp3",
        "sunset_dreams.mp3",
    ]
    assert all(not row["music"].startswith("track_") for row in rows)


def test_add_music_to_library_updates_csv(tmp_path):
    sample_dir = tmp_path / "music"
    sample_dir.mkdir()
    csv_path = tmp_path / "music.csv"

    source_file = tmp_path / "source_track.mp3"
    source_file.write_text("sample mp3 content", encoding="utf-8")

    rows = add_music_to_library(source_file, music_dir=sample_dir, csv_path=csv_path)

    assert (sample_dir / "source_track.mp3").exists()
    assert len(rows) == 1
    assert rows[0]["music"] == "source_track.mp3"
    assert rows[0]["location"] == str((sample_dir / "source_track.mp3").resolve())


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
    assert (sample_dir / "sample_track_1.mp3").exists()
    assert (sample_dir / "sample_track_2.mp3").exists()
    assert all(not row["music"].startswith("track_") for row in rows)


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
            self.volume = None

        def set_mrl(self, file_path):
            self.paths.append(file_path)
            self._playing = True

        def audio_set_volume(self, volume):
            self.volume = volume

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

    music_player(sample_dir, max_passes=1, csv_path=csv_path, volume=100)

    assert len(fake_player.paths) == len(sample_files)
    assert all(path.endswith((".mp3", ".wav")) for path in fake_player.paths)
    assert fake_player.volume == 100

    with csv_path.open("r", encoding="utf-8", newline="") as csv_file:
        rows = list(csv.DictReader(csv_file))

    assert rows
    assert rows[0]["music"] in {"track1.mp3", "track1.wav"}
    assert "Enjoy" in rows[0]["intro"]
    assert "size" in rows[0]
    assert "location" in rows[0]


def test_music_player_ramps_volume_up_while_playing(tmp_path, monkeypatch):
    sample_dir = tmp_path / "music"
    sample_dir.mkdir()

    sample_files = [
        sample_dir / "track1.mp3",
        sample_dir / "track2.mp3",
    ]

    for sample in sample_files:
        sample.write_text("sample mp3 content", encoding="utf-8")

    csv_path = tmp_path / "music.csv"

    class FakeMediaPlayer:
        def __init__(self):
            self.calls = []
            self._playing = True
            self.volume = None

        def set_mrl(self, file_path):
            self.volume = None

        def audio_set_volume(self, volume):
            self.calls.append(volume)
            self.volume = volume

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

    music_player(sample_dir, max_passes=1, csv_path=csv_path, volume=100)

    assert fake_player.volume == 100
    assert len(fake_player.calls) >= 2
    assert fake_player.calls[0] < 100


def test_music_player_waits_for_track_after_initial_startup_delay(
    tmp_path, monkeypatch
):
    sample_dir = tmp_path / "music"
    sample_dir.mkdir()
    sample_files = [sample_dir / "track1.wav", sample_dir / "track2.wav"]

    for sample in sample_files:
        sample.write_text("sample mp3 content", encoding="utf-8")

    csv_path = tmp_path / "music.csv"

    class FakeMediaPlayer:
        def __init__(self):
            self.paths = []
            self.polls = 0

        def set_mrl(self, file_path):
            self.paths.append(file_path)
            self.polls = 0

        def audio_set_volume(self, volume):
            pass

        def play(self):
            pass

        def is_playing(self):
            self.polls += 1
            return self.polls > 1 and self.polls < 4

    fake_player = FakeMediaPlayer()
    monkeypatch.setitem(
        sys.modules,
        "vlc",
        SimpleNamespace(
            Instance=lambda: SimpleNamespace(media_player_new=lambda: fake_player)
        ),
    )

    music_player(sample_dir, max_passes=1, csv_path=csv_path, volume=100)

    assert len(fake_player.paths) == len(sample_files)


def test_play_randomized_music_from_folder_uses_randomized_playlist(
    tmp_path, monkeypatch
):
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
            self.volume = None

        def set_mrl(self, file_path):
            self.paths.append(file_path)
            self._playing = True

        def audio_set_volume(self, volume):
            self.volume = volume

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

    play_randomized_music_from_folder(sample_dir, max_passes=1, csv_path=csv_path)

    assert len(fake_player.paths) == len(sample_files)
    assert all(path.endswith(".mp3") for path in fake_player.paths)


def test_music_player_releases_vlc_resources_after_track(tmp_path, monkeypatch):
    sample_dir = tmp_path / "music"
    sample_dir.mkdir()
    (sample_dir / "track.mp3").write_text("sample mp3 content", encoding="utf-8")
    csv_path = tmp_path / "music.csv"

    class FakeMediaPlayer:
        def __init__(self):
            self.stopped = False
            self.released = False
            self._playing = True

        def set_mrl(self, file_path):
            pass

        def audio_set_volume(self, volume):
            pass

        def play(self):
            self._playing = True

        def is_playing(self):
            if self._playing:
                self._playing = False
                return True
            return False

        def stop(self):
            self.stopped = True

        def release(self):
            self.released = True

    fake_player = FakeMediaPlayer()
    fake_instance = SimpleNamespace(
        media_player_new=lambda: fake_player,
        release=lambda: setattr(fake_instance, "released", True),
        released=False,
    )
    monkeypatch.setitem(
        sys.modules,
        "vlc",
        SimpleNamespace(Instance=lambda: fake_instance),
    )

    music_player(sample_dir, max_passes=1, csv_path=csv_path)

    assert fake_player.stopped is True
    assert fake_player.released is True
    assert fake_instance.released is True


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
