import sys
import os
import tomllib
import platform


def main():
    if len(sys.argv) >= 3 and sys.argv[2] != "--pre" and False:
        orig = os.path.abspath(sys.argv[2])
    else:
        for i in os.listdir(
            os.path.join(
                os.path.abspath(os.path.dirname(__file__)),
                "..",
                "dist",
            )
        ):
            if i.startswith("ppb"):
                orig = os.path.abspath(
                    os.path.join(
                        os.path.dirname(__file__), "..", "dist", i
                    )
                )
                break
        else:
            raise FileNotFoundError
    if len(sys.argv) >= 3 and sys.argv[2] != "--pre":
        pyver = sys.argv[2]
    else:
        pyver = "unknown-python"
    if len(sys.argv) >= 2 and sys.argv[1] != "--pre":
        ver = sys.argv[1]
    else:
        d = tomllib.load(
            open(
                os.path.join(
                    os.path.dirname(__file__), "..", "pyproject.toml"
                ),
                "rb",
            )
        )
        ver = d["project"]["version"]
    if platform.platform() == "Linux":
        sys_platform = "linux"
    else:
        sys_platform = "windows"
    root, ext = os.path.splitext(os.path.basename(orig))
    if ext == "" or ext is None:
        if "--pre" in sys.argv:
            new_name = f"{root}_{pyver}_pre-{ver}_{sys_platform}.bin"
        else:
            new_name = f"{root}_{pyver}_{ver}_{sys_platform}.bin"
    else:
        if "--pre" in sys.argv:
            new_name = f"{root}_{pyver}_pre-{ver}_{sys_platform}{ext}"
        else:
            new_name = f"{root}_{pyver}_{ver}_{sys_platform}{ext}"
    if platform.platform() == "Linux":
        new_name = f"{new_name}.bin"
    new_path = os.path.join(os.path.dirname(orig), new_name)
    os.rename(orig, new_path)
    print(new_path)


if __name__ == "__main__":
    main()
