import argparse

import func.function as fnf


def _print_header(title):
    print("\n" + "=" * 60)
    print(title.center(60))
    print("=" * 60)


def main(play_immediately=False):
    if play_immediately:
        fnf.music_player()
        return

    _print_header("WELCOME TO MUSIC MIXER")
    print(
        "A simple music player with shuffle, looping, admin controls, and CSV tracking."
    )

    while True:
        print("\nMain Menu")
        print("[1] Play music")
        print("[2] Manage music library")
        print("[3] View music library")
        print("[4] Exit")

        try:
            choice = input("\nChoose an option (1-4): ").strip()
        except (EOFError, KeyboardInterrupt):
            print("\nGoodbye!")
            break

        if choice == "1":
            try:
                fnf.music_player()
            except Exception as exc:
                print(f"\nError: {exc}")
        elif choice == "2":
            try:
                fnf.admin()
            except KeyboardInterrupt:
                print("\nAdmin panel closed.")
            except Exception as exc:
                print(f"\nError: {exc}")
        elif choice == "3":
            try:
                rows = fnf.sync_music_csv()
                if not rows:
                    print("\nNo songs found in the music folder.")
                else:
                    print("\nMusic Library")
                    for row in rows:
                        print(
                            f"{row['index']}. {row['music']} | "
                            f"Size: {row['size']} | "
                            f"Location: {row['location']}"
                        )
            except Exception as exc:
                print(f"\nError: {exc}")
        elif choice == "4":
            print("\nThanks for using Music Mixer. Goodbye!")
            break
        else:
            print("\nInvalid option. Enter 1, 2, 3, or 4.")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Play and manage your music library.")
    parser.add_argument(
        "--play",
        action="store_true",
        help="start playing music immediately",
    )
    args = parser.parse_args()
    main(play_immediately=args.play)
