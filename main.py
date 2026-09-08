import func.function as fnf
from sys import exit


def main():
    print()
    print("=" * (40 - 12))
    print("|  Welcome to music player |")
    print("=" * (40 - 12), "\n")

    choice = input("Enter for playing the music ")

    if choice:
        fnf.admin()
    else:
        print("Playing music")


if __name__ == "__main__":
    main()
