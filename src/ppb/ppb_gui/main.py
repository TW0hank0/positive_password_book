import os
import subprocess

from . import unpack_addons


def main():
    unpack_addons.main()
    gui_dir: str = os.path.join(os.path.dirname(__file__), "exports")
    if os.name == "nt":
        gui_file = os.path.join(
            gui_dir, "win", "ppb_gui_win_x86-64.exe"
        )
    else:
        gui_file = os.path.join(
            gui_dir, "linux", "ppb_gui_linux.x86_64"
        )
    subprocess.run(gui_file)


if __name__ == "__main__":
    main()
