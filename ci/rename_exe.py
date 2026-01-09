import sys
import os
import tomllib
import platform


def main():
    if len(sys.argv) >= 3 and sys.argv[2] != "--pre":
        orig = os.path.abspath(sys.argv[2])
    else:
        for i in os.listdir(
            os.path.join(os.path.abspath(os.path.dirname(__file__)), "..", "dist")
        ):
            if i.startswith("positive_password_book"):
                orig = os.path.abspath(
                    os.path.join(os.path.dirname(__file__), "..", "dist", i)
                )
                break
        else:
            raise FileNotFoundError
    if len(sys.argv) >= 4 and sys.argv[3] != "--pre":
        pyver = sys.argv[3]
    else:
        pyver = "unknown"
    if len(sys.argv) >= 2 and sys.argv[1] != "--pre":
        ver = sys.argv[1]
    else:
        d = tomllib.load(
            open(os.path.join(os.path.dirname(__file__), "..", "pyproject.toml"), "rb")
        )
        ver = d["project"]["version"]
    root, ext = os.path.splitext(os.path.basename(orig))
    if ext == "" or ext is None:
        if "--pre" in sys.argv:
            new_name = f"{root}_{pyver}_pre-{ver}.bin"
        else:
            new_name = f"{root}_{pyver}_{ver}.bin"
    else:
        if "--pre" in sys.argv:
            new_name = f"{root}_{pyver}_pre-{ver}{ext}"
        else:
            new_name = f"{root}_{pyver}_{ver}{ext}"
    if platform.platform() == "Linux":
        new_name = f"{new_name}.bin"
    new_path = os.path.join(os.path.dirname(orig), new_name)
    os.rename(orig, new_path)
    print(new_path)


if __name__ == "__main__":
    main()
