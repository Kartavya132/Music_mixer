import func.function as fnf


def main():
    print()
    print("=" * (40 - 12))
    print("|  Welcome to music player |")
    print("=" * (40 - 12), "\n")

    input("Press Enter to start playing music from the music folder... ")
    fnf.music_player()


if __name__ == "__main__":
    main()
