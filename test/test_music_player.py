from pathlib import Path

from func.function import music_player


def test_music_player_with_sample_mp3_files(tmp_path):
    sample_dir = tmp_path / "music"
    sample_dir.mkdir()

    sample_files = [
        sample_dir / "track1.mp3",
        sample_dir / "track2.mp3",
        sample_dir / "track3.mp3",
    ]

    for sample in sample_files:
        sample.write_text("sample mp3 content", encoding="utf-8")

    try:
        music_player(sample_dir)
    except Exception as exc:
        assert "No .mp3 files found" not in str(exc)
        assert "pygame is required" in str(exc) or "Could not initialize" in str(exc)
