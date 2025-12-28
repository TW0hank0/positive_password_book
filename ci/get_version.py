import tomllib
import os


def main():
    d = tomllib.load(
        open(os.path.join(os.path.dirname(__file__), "..", "pyproject.toml"), "rb")
    )
    # v = d.get("project", {}).get("version") or d.get("tool", {}).get("poetry", {}).get(
    # "version"
    # )
    v = d.get("project", {}).get("version")
    print(v)


main()
