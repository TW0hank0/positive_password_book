import json

from positive_tool.arg import ArgType


class PasswordBookSystem:
    def __init__(self, file_path: str | None = None) -> None:
        if file_path is None:
            self.password_book_new()
        else:
            self.password_book_load(file_path)
        # self._data: dict[str, list[dict[str, str]]] | None = None

    def password_book_new(self):
        # ArgType("file_path", file_path, str, is_exists=False, is_file=True)
        #
        self._data = {"trash_can": []}

    def password_book_load(self, file_path: str):
        ArgType("file_path", file_path, str, is_exists=True, is_file=True)
        #
        with open(file_path, "r", encoding="utf-8") as f:
            file_data: dict = json.load(f)
        if type(file_data) is not dict:
            raise TypeError()
        # for i in file_data.keys():
        # if type(i) is not str or type(file_data[i]) is not list:
        # raise TypeError()
        self._data = file_data

    def password_book_save(self, file_path: str):
        if self._data is None:
            raise TypeError()
        #
        with open(file_path, "w", encoding="utf-8") as f:
            json.dump(self._data, f, ensure_ascii=False, indent=4)

    def password_book_insert(
        self, app_name: str, acc: str, pwd: str, *, note: str = "", user_note: str = ""
    ):
        #
        ArgType("app_name", app_name, str)
        ArgType("acc", acc, str)
        ArgType("pwd", pwd, str)
        ArgType("note", note, str)
        ArgType("user_note", user_note, str)
        if self._data is None:
            raise TypeError()
        #
        app_data = {"acc": acc, "pwd": pwd, "note": note, "user_note": user_note}
        app_exists: bool = False
        for i in list(self._data.keys()):
            if app_name == i:
                app_exists = True
                break
        if app_exists is True:
            self._data[app_name].append(app_data)
        else:
            self._data[app_name] = [app_data]

    def password_book_delete(self, app_name: str, acc: str) -> None:
        #
        ArgType("app_name", app_name, str)
        ArgType("acc", acc, str)
        if self._data is None:
            raise TypeError()
        #
        if app_name not in self._data.keys():
            raise IndexError()
        else:
            acc_exists: bool = False
            index: int = 0
            for i in self._data[app_name]:
                if acc == i["acc"]:
                    acc_exists = True
                    break
                else:
                    index += 1
            if acc_exists is True:
                del self._data[app_name][index]
                if len(self._data[app_name]) <= 0:
                    del self._data[app_name]
            else:
                raise IndexError()

    def password_book_move_to_trash_can(self, app: str, acc: str):
        if app in list(self._data.keys()):
            for i in self._data[app]:
                if i["acc"] == acc:
                    break
            else:
                raise IndexError()
        else:
            raise KeyError()

    def password_book_get_data(self) -> dict:
        return self._data

    def password_book_search(self, app: str) -> list | None:
        if app != "trash_can" and app in list(self._data.keys()):
            app_datas: list = self._data[app]
            return app_datas
        else:
            return None

    def __str__(self) -> str:
        return f"""PasswordBookSystem(_data={self._data})"""
