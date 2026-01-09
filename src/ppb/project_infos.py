import os
import tomllib
import sys

from typing import Any, Union, Literal

from positive_tool import pt


_PROJECT_NAME = "positive_password_book"
# _project_path = pt.find_project_path(
#     _PROJECT_NAME, start_find_path=os.path.dirname(__file__)
# )
if hasattr(sys, "_MEIPASS") is True:
    _project_path = os.path.dirname(sys.executable)
else:
    _project_path = pt.find_project_path(_PROJECT_NAME, os.path.dirname(__file__))

_project_info_file_path = os.path.join(_project_path, "pyproject.toml")

with open(_project_info_file_path, "rb") as f:
    _project_info = tomllib.load(f)
_version = _project_info["project"]["version"]

project_infos_type = dict[
    Union[
        str,
        Literal[
            "version",
            "project_path",
            "project_info_file_path",
            "project_name",
            "project_info",
        ],
    ],
    Union[str, Any],
]
project_infos: project_infos_type = {
    "version": _version,
    "project_path": _project_path,
    "project_info_file_path": _project_info_file_path,
    "project_name": _PROJECT_NAME,
    "project_info": _project_info,
}
