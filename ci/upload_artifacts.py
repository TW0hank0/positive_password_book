import os
import subprocess
import sys

path = os.path.join(os.path.dirname(__file__), "..", "artifacts")
dirs = os.listdir(path)
for dir in dirs:
    print(f"dir now: {dir}")
    if (os.path.isfile(dir)) is True or (os.path.isdir(dir) is False):
        full_path = os.path.join(path, dir)
        print(f"uploading {dir}")
        subprocess.run(
            [
                "gh",
                "release",
                "upload",
                sys.argv[1],
                full_path,
                f"--repo={sys.argv[2]}",
            ],
            check=True,
            timeout=40.0,
        )
    else:
        print("dir files:{}".format(os.listdir(os.path.join(path, dir))))
