import shutil
import os


def main():
    if os.name == "nt":  # Windows
        appdata_path = os.path.join(
            os.environ["APPDATA"], "Local", "ppb"
        )
    else:  # Linux
        appdata_path = os.path.join(
            os.path.expanduser("~"), ".local", "ppb"
        )
    os.makedirs(appdata_path, exist_ok=True)
    addon_backend_path = os.path.join(
        appdata_path, "addons", "ppb_backend"
    )
    target_backend_dir = os.path.join(
        os.path.dirname(__file__), "addons", "ppb_backend"
    )
    if os.name == "nt":
        target_backend_file = os.path.join(
            target_backend_dir, "ppb_backend_win.exe"
        )
    else:
        target_backend_file = os.path.join(
            target_backend_dir, "ppb_backend_linux"
        )
    shutil.copy2(target_backend_file, addon_backend_path)


if __name__ == "__main__":
    main()
