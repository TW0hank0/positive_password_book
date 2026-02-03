import json
# import os

from typing import Literal, Union

# import typer

from positive_tool.verify import ArgType
from positive_tool import pt

# from ..project_infos import project_infos
from ..ppb_errors import error_backend

data_type = dict[
    str,
    list[
        dict[
            Union[
                Literal[
                    "acc",
                    "pwd",
                    "note",
                    "usernote",
                    "email",
                    "recovery-code",
                ],
                str,
            ],
            str,
        ]
    ],
]


class PasswordBookSystem:
    _data: data_type

    @ArgType.auto()
    def __init__(self, data: dict) -> None:
        self._data = data

    @classmethod
    def password_book_new(cls):
        cls({"trash_can": []})

    # def password_book_new_old(self):
    #     # ArgType("file_path", file_path, str, is_exists=False, is_file=True)
    #     #
    #     self._data = {"trash_can": []}

    @classmethod
    def password_book_load(cls, file_path: str):
        ArgType("file_path", file_path, str, is_exists=True, is_file=True)
        #
        with open(file_path, "r", encoding="utf-8") as f:
            file_data: dict = json.load(f)
        if type(file_data) is not dict:
            raise error_backend.FileContentError("資料類型錯誤！")
        else:
            cls(file_data)

    # def password_book_load_old(self, file_path: str):
    #     ArgType("file_path", file_path, str, is_exists=True, is_file=True)
    #     #
    #     with open(file_path, "r", encoding="utf-8") as f:
    #         file_data: dict = json.load(f)
    #     if type(file_data) is not dict:
    #         raise error_backend.FileContentError("資料類型錯誤！")
    #     self._data = file_data

    def password_book_save(self, file_path: str):
        if self._data is None:
            raise error_backend.BackendSaveError("儲存失敗：資料為None")
        else:
            with open(file_path, "w", encoding="utf-8") as f:
                json.dump(
                    self._data,
                    f,
                    ensure_ascii=False,
                    indent=4,
                    sort_keys=True,
                )

    def password_book_insert(
        self,
        app_name: str,
        acc: str,
        pwd: str,
        *,
        note: str = "",
        user_note: str = "",
    ):
        #
        ArgType("app_name", app_name, str)
        ArgType("acc", acc, str)
        ArgType("pwd", pwd, str)
        ArgType("note", note, str)
        ArgType("user_note", user_note, str)
        # if self._data is None:
        #     raise TypeError()
        #
        app_data = {
            "acc": acc,
            "pwd": pwd,
            "note": note,
            "user_note": user_note,
        }
        for i in list(self._data.keys()):
            if app_name == i:
                app_exists = True
                break
        else:
            app_exists: bool = False
        if app_exists is True:
            self._data[app_name].append(app_data)
        else:
            self._data[app_name] = [app_data]

    def password_book_delete(self, app_name: str, acc: str) -> None:
        #
        ArgType("app_name", app_name, str)
        ArgType("acc", acc, str)
        # if self._data is None:
        #     raise TypeError()
        #
        if app_name not in self._data.keys():
            raise error_backend.BackendDeleteError(
                "錯誤：資料(app)不存在！"
            )
        else:
            index = pt.UInt(0)
            for i in self._data[app_name]:
                if acc == i["acc"]:
                    acc_exists = True
                    break
                else:
                    index += 1
            else:
                acc_exists: bool = False
            if acc_exists is True:
                del self._data[app_name][int(index)]
                if len(self._data[app_name]) <= 0:
                    del self._data[app_name]
            else:
                raise error_backend.BackendDeleteError(
                    "錯誤：資料(acc)不存在！"
                )

    def password_book_move_to_trash_can(self, app: str, acc: str):
        # TODO:finish it
        if app in list(self._data.keys()):
            for i in self._data[app]:
                if i["acc"] == acc:
                    break
            else:
                raise IndexError()
        else:
            raise KeyError()

    def password_book_get_data(self) -> dict:
        return self._data.copy()

    def password_book_search(self, app: str) -> list | None:
        # TODO:finish it
        if app != "trash_can" and app in list(self._data.keys()):
            app_datas: list = self._data[app]
            return app_datas
        else:
            return None

    def __str__(self) -> str:
        return f"""PasswordBookSystem(_data={self._data})"""
