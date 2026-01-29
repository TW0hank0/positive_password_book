import os
import subprocess
import sys

dirs = os.listdir(os.path.join(os.path.dirname(__file__), "..", "artifacts"))
for dir in dirs:
    print(f"dir now: {dir}")
    if (os.path.isfile(dir)) is True or (os.path.isdir(dir) is False):
        print(f"uploading {dir}")
        full_path = os.path.join(
            os.path.join(os.path.dirname(__file__), "arttifacts"), dir
        )
        subprocess.run(
            ["gh", "release", "upload", sys.argv[1], dir, f"--repo={sys.argv[2]}"]
        )
    else:
        print(
            "dir files:{}".format(
                os.listdir(
                    os.path.join(os.path.dirname(__file__), "..", "artifacts", dir)
                )
            )
        )
