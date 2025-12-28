import sys
import os


def main():
    orig = sys.argv[1]
    ver = sys.argv[2]
    root, ext = os.path.splitext(os.path.basename(orig))
    new_name = f"{root}_{ver}.{ext}"
    new_path = os.path.join(os.path.dirname(orig), new_name)
    os.rename(orig, new_path)
    print(new_path)


if __name__ == "__main__":
    main()
