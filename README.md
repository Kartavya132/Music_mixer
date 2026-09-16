# Music Mixer

A stylish, terminal-based music player project that lets you build a personal music library, shuffle songs in a loop, manage tracks, and enjoy your playlist with a smooth, no-fuss flow.

## 🎵 What this project does

Music Mixer is designed for people who want a simple home music experience with a few useful controls:

- Add songs to a local music folder
- Automatically track and organize files in a CSV library
- Shuffle songs in a loop for continuous playback
- Manage the library with an admin panel
- View the music collection from the terminal UI
- Play tracks using VLC with a strong max-volume startup flow

## ✨ Core features

- Smart playlist generation from the local `music` folder
- CSV-backed music library tracking
- Randomized playback loop
- Admin panel for adding and deleting songs
- Library listing with metadata like name, size, and location
- Easy startup through the launcher and main menu
- Playback volume ramping to a clean, loud listening experience

## 🧩 Project structure

```text
Music_mixer/
├── main.py                  # Terminal menu and app entry
├── music_launcher.py        # Launches the app in immediate-play mode
├── music.spec              # PyInstaller spec file for packaging
├── README.md               # Project documentation
├── func/
│   ├── function.py         # Core music logic
│   └── music.csv          # Generated music catalog
├── music/                  # Actual music files
├── test/
│   └── test_music_player.py
├── build/
│   └── music/             # PyInstaller build output
└── .gitignore              # Project ignore rules (if present)
```

## 🔧 Main files

### `main.py`
Handles the user menu and app flow:

- Play music
- Open admin panel
- Show library
- Exit the app

### `music_launcher.py`
Starts the app directly in play mode.

### `func/function.py`
Contains the real app logic:

- scanning files
- generating CSV entries
- adding/removing music
- playlist selection
- VLC playback control
- volume management

### `func/music.csv`
Stores discovered song metadata in a structured table for easy management.

### `test/test_music_player.py`
Contains automated tests for music discovery, CSV updates, playback, and player lifecycle.

## 🚀 How to run

### 1. Install dependencies

Make sure Python is installed, then install VLC support:

```bash
py -m pip install python-vlc
```

### 2. Run the app

```bash
py main.py
```

Or start immediately in playback mode:

```bash
py music_launcher.py
```

## 🎮 How it works

1. The app scans the `music` folder.
2. It creates a library list and saves it to `func/music.csv`.
3. You can play the shuffled playlist in a loop.
4. The admin panel helps add or remove songs.
5. VLC plays each track with a volume ramp-up for a cleaner startup.

## 🗂️ Library management

The project supports:

- viewing all songs in the library
- adding `.mp3` files from your system
- deleting tracks from the local `music` folder
- reindexing the CSV data automatically after changes

## ✅ Current capabilities

This project already supports:

- music discovery
- playlist looping
- random shuffle playback
- CSV-based library tracking
- admin management tools
- safe playback stop and cleanup
- max-volume startup behavior

## 💡 Future improvements

This app could be expanded with features like:

- a better visual interface with Tkinter or PyQt
- album art support
- song search and filtering
- volume controls during playback
- favorite and recently played lists
- drag-and-drop library import
- dark-mode terminal UI

## 🧪 Testing

Run tests with:

```bash
py -m pytest -q
```

These tests cover:

- CSV generation
- adding songs
- playback flow
- randomization
- lifecycle cleanup

## 📌 Summary

Music Mixer is a compact yet capable music playback application that balances simplicity, organization, and automation. It turns a local folder of songs into a mini personal music library with shuffle, loop playback, and easy track management.

If you want, this project can evolve into a richer desktop-style music app with a GUI, album covers, and a more polished user experience.
