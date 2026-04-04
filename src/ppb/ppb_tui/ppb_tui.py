import json
import logging
import os
import sys
import time
from typing import Any, Callable, Literal

from positive_tool import pt
from positive_tool.verify import ArgType
from rich.console import Console
from rich.containers import Renderables
from rich.layout import Layout
from rich.panel import Panel
from rich.prompt import Confirm, Prompt, PromptBase
from rich.rule import Rule
from rich.style import Style
from rich.table import Table
from rich.text import Text
from rich.tree import Tree

from ...ppb.project_infos import project_infos
from ..ppb_backend import ppb_backend
from ..ppb_errors import error_backend

project_name: str = project_infos.project_name
license_file_path = project_infos.project_license_file_path
project_path = project_infos.project_path


class PPBActionPrompt(PromptBase[str]):
    def __init__(
        self,
        prompt: str | Text = "",
        *,
        console: Console | None = None,
        password: bool = False,
        choices: list[str] | None = None,
        case_sensitive: bool = True,
        show_default: bool = True,
        show_choices: bool = True,
    ) -> None:
        super().__init__(
            prompt,
            console=console,
            password=password,
            choices=choices,
            case_sensitive=case_sensitive,
            show_default=show_default,
            show_choices=show_choices,
        )

    def process_response(self, value: str) -> str:
        return value


class PPBLogHandler(logging.Handler):
    def __init__(self, console: Console, level=logging.INFO):
        super().__init__(level)
        self.console = console
        self.logs = []  # 存儲日誌的列表
        self.max_logs = 50  # 最大日誌數量
        # 設置日誌格式
        self.formatter = logging.Formatter(
            "%(asctime)s | %(levelname)s | %(message)s",
            datefmt="%H:%M:%S",
        )

    def emit(self, record):
        try:
            msg = self.format(record)
            # 添加到日誌列表
            self.logs.append(msg)
            # 限制日誌數量
            if len(self.logs) > self.max_logs:
                self.logs.pop(0)
        except Exception:
            self.handleError(record)

    def get_log_content(self):
        renderables_list = []
        recent_logs: list = (
            self.logs[self.console.size.height - 7 :]
            if len(self.logs) > (self.console.size.height - 7)
            else self.logs
        )
        for log in recent_logs:
            # 根據日誌等級設置顏色
            if "CRITICAL" in log:
                log_text = Text(
                    log, style=Style(color="bright_red", bold=True)
                )
            elif "ERROR" in log:
                log_text = Text(log, style=Style(color="bright_red"))
            elif "WARNING" in log:
                log_text = Text(log, style=Style(color="bright_yellow"))
            elif "INFO" in log:
                log_text = Text(log, style=Style(color="yellow", dim=True))
            elif "DEBUG" in log:
                log_text = Text(log, style=Style(color="blue"))
            else:
                log_text = Text(log, style=Style(color="white"))
            renderables_list.append(log_text)
        renderables_list.reverse()
        return Renderables(renderables_list)

    def get_logs(self) -> list:
        return self.logs.copy()


class PPBSetting:
    init_setting: dict = {"acc_tree__tree_type": "same_line"}

    def __init__(
        self,
        setting_file_path: str | os.PathLike,
        logger: logging.Logger,
        mode: Literal["load", "new", "auto"] = "auto",
    ) -> None:
        #
        ArgType("setting_file_path", setting_file_path, [str, os.PathLike])
        ArgType("mode", mode, ["load", "new", "auto"])
        #
        self.setting_file_path: str = str(setting_file_path)
        self.logger: logging.Logger = logger
        self.data: dict[str, Any] = self.init_setting.copy()
        #
        if mode == "auto":
            self.setting_auto()

    def setting_load(self) -> None:
        if (
            os.path.exists(self.setting_file_path) is True
            and os.path.isfile(self.setting_file_path) is True
            and (
                self._bytes_to_mb(os.path.getsize(self.setting_file_path))
                < 10
            )  # 確保檔案不會過大
        ):
            with open(self.setting_file_path, "r", encoding="utf-8") as f:
                try:
                    setting_file = json.load(f)
                except json.JSONDecodeError as e:
                    self.logger.error(f"設定解析錯誤：{e}")
                else:
                    self.data.update(
                        setting_file
                    )  # TODO: 待增加key、value判定（數據類型、合法key）
            return None

    def setting_auto(self):
        if os.path.exists(
            self.setting_file_path
        ) is True and os.path.isfile(self.setting_file_path):
            self.setting_load()
        else:
            self.setting_save()

    def setting_save(self) -> None:
        with open(self.setting_file_path, "w", encoding="utf-8") as f:
            json.dump(
                self.data,
                f,
                ensure_ascii=False,
                sort_keys=True,
                indent=4,
            )

    def _bytes_to_mb(self, bytes: int) -> float:
        return (bytes / 1000) / 1000

    def __getitem__(self, key: str):
        ArgType("key", key, [str])
        #
        if key in list(self.data.keys()):
            return self.data[key]
        else:
            self.logger.error(f"找不到設定的key：{key}")
            sys.exit(1)


class PPBTUIDataBackend:
    def __init__(self, file_path: str, logger: logging.Logger) -> None:
        self.file_path = file_path
        self.logger = logger
        if os.path.exists(file_path) is True:
            if ppb_backend.get_is_file_encrypt(file_path) is False:
                self.backend = (
                    ppb_backend.PasswordBookSystem.password_book_load(
                        file_path
                    )
                )
                self.is_encrypt = False
            else:
                self.console = Console()
                while True:
                    encrypt_password = Prompt.ask(
                        "[PPB] (quit退出) (不顯示) 輸入密碼",
                        password=True,
                    )
                    if encrypt_password in ["quit", "退出"]:
                        sys.exit()
                    else:
                        try:
                            self.backend = ppb_backend.PasswordBookSystem.load_encrypt(
                                file_path, encrypt_password
                            )
                        except error_backend.BackendWrongPassword:
                            msg = "密碼錯誤！"
                            self.logger.warning(msg)
                            self.console.print(f"[yelow]{msg}[/yellow]")
                        else:
                            if (
                                type(self.backend)
                                is ppb_backend.PasswordBookSystem
                            ):
                                self.encrypt_password = encrypt_password
                                self.is_encrypt = True
                                break
                            else:
                                msg = "資料回傳錯誤！"
                                self.logger.warning(msg)
                                self.console.print(
                                    f"[yellow]{msg}[/yellow]"
                                )
        else:
            self.backend = (
                ppb_backend.PasswordBookSystem.password_book_new()
            )

    def save(self):
        if self.backend is not None:
            if self.is_encrypt is True:
                self.backend.save_encrypt(
                    self.file_path, self.encrypt_password
                )
            else:
                self.backend.password_book_save(self.file_path)
        else:
            self.logger.error("save error")

    def save_to_encrypt(self, encrypt_password: str):
        if self.backend is not None:
            self.backend.save_encrypt(self.file_path, encrypt_password)
        else:
            self.logger.error("save error")

    def save_to_no_encrypt(self):
        if self.backend is not None:
            self.backend.password_book_save(self.file_path)
        else:
            self.logger.error("save error")

    def get_data(self):
        if self.backend is not None:
            return self.backend.password_book_get_data()
        else:
            self.logger.error("資料回傳錯誤！")
            return {}

    def insert_data(
        self,
        app: str,
        acc: str,
        pwd: str,
        usernote: str = "",
        note: str = "",
    ):
        if self.backend is not None:
            self.backend.password_book_insert(
                app, acc, pwd, note=note, user_note=usernote
            )
        else:
            self.logger.error("insert error")

    def delete_data(self, app, acc):
        if self.backend is not None:
            self.backend.password_book_delete(app, acc)
        else:
            self.logger.error("delete error")


class PPBTUIAction:
    __slots__ = ("name", "alias", "call")

    def __init__(
        self,
        act_name: str,
        act_alias: list[str],
        act_call: Callable | None = None,
    ) -> None:
        self.name = act_name
        self.alias = act_alias
        self.call = act_call


class PasswordBook:
    def __init__(self, logger: logging.Logger, version) -> None:
        self.console = Console()
        self.logger: logging.Logger = logger
        self.ppb_tui_log_handler = PPBLogHandler(console=self.console)
        self.logger.addHandler(self.ppb_tui_log_handler)
        self.version = version
        self.data_file_path: str = os.path.abspath(
            os.path.join(project_path, "password_data.json")
        )
        self.data_backend = PPBTUIDataBackend(
            self.data_file_path, self.logger
        )
        self.data: ppb_backend.data_type = {}
        self.pages: list = []
        self.setting_file_path = os.path.abspath(
            os.path.join(project_path, "setting_tui.json")
        )
        self.setting = PPBSetting(self.setting_file_path, self.logger)
        self.left_change_unsave: bool = False
        self.content_per_page: int = self.console.size.height - 13
        self.page_num = 0
        self.page_max_num = 0
        #
        self.get_backend_data()
        self.refresh_page()
        #
        self.main()

    def get_backend_data(self):
        # self.data = self.backend.password_book_get_data()
        self.data = self.data_backend.get_data()
        self.refresh_page()

    def backend_save_data(self):
        # self.backend.password_book_save(self.data_file_path)
        self.data_backend.save()

    def print_data(self, clear_scrren: bool = False):
        self.logger.debug(f"所有分頁： {self.pages}")
        self.logger.debug(f"資料： {self.data}")
        self.logger.debug(f"總頁數： {self.page_max_num}")
        #
        if clear_scrren is True:
            self.console.clear()
        page_info = Text(
            f"第{self.page_num}頁，共{self.page_max_num}頁",
            style=Style(),
        )
        version_text = f"版本：{self.version}"
        version_info = Text(version_text, justify="center")
        info_rule = Rule(style=Style(color="green", dim=True))
        infos = Renderables([page_info])
        #
        if len(self.pages) > 0 and self.page_max_num > 0:
            tree = Tree(
                "資料", style=Style(color="bright_blue", bold=True)
            )
            for app, app_data in self.pages[self.page_num - 1]:
                self.logger.debug(f"app:{app}, app_data:{app_data}")
                if app == "trash_can":
                    continue
                else:
                    child_tree = self.acc_tree(app, app_data["acc"])
                    tree.children.append(child_tree)
            content = Renderables([infos, info_rule, tree])
        else:
            content = Renderables(
                [
                    infos,
                    info_rule,
                    Text("無資料", style=Style(italic=True)),
                ]
            )
        log_panel_width = int(self.console.size.width / 3)
        content_panel_width = self.console.width - log_panel_width
        layout = Layout()
        layout.split_row(
            Panel(
                content,
                title="資料",
                width=content_panel_width,
                height=self.console.size.height - 7,
            )
        )
        log_content = self.ppb_tui_log_handler.get_log_content()
        log_panel = Panel(
            log_content,
            title="日誌",
            width=log_panel_width,
            height=self.console.size.height - 7,
            # width=int((self.console.size.width - 4) / 3),
        )
        i = Layout(size=log_panel_width)
        i.split_row(log_panel)
        layout.add_split(i)
        all_contents = Renderables([version_info, layout])
        self.console.print(
            Panel(
                all_contents,
                title=Text(
                    project_name,
                    style=Style(color="rgb(175, 0, 255)", bold=True),
                ),
                height=self.console.size.height - 3,
                border_style=Style(color="green"),
            )
        )

    def refresh_page(self):
        if (self.data is None) or (isinstance(self.data, dict) is False):
            self.get_backend_data()
        #
        self.logger.debug(f"每頁內容數： {self.content_per_page}")
        self.logger.debug(f"資料： {self.data}")
        self.logger.debug(f"資料keys： {list(self.data.keys())}")
        #
        self.pages.clear()
        count = pt.UInt(1)
        page: list = []
        for app in list(self.data.keys()):
            if app == "trash_can":
                continue
            self.logger.debug(f"key -> app： {app}")
            app_datas = self.data[app]
            self.logger.debug(f"value -> app_datas： {app_datas}")
            for app_data in app_datas:
                page.append((app, app_data))
                self.logger.debug(f"page： {page}")
                if (count + 5 + 5) >= self.content_per_page:
                    self.pages.append(page.copy())
                    self.logger.debug(
                        f"pages -> self.pages： {self.pages}"
                    )
                    page.clear()
                    count = pt.UInt(1)
                else:
                    count += 5  # 五個value
        self.logger.debug(f"page： {page}")
        if len(page) > 0:
            self.pages.append(page.copy())
            page.clear()
        self.page_num = 1
        self.page_max_num = len(self.pages)
        self.logger.debug(f"pages -> self.pages： {self.pages}")

    def close(self):
        self.backend_save_data()
        sys.exit()

    def insert_appdata(self):
        self.console.clear()
        self.console.print(
            Rule(
                Text(project_name, style=Style(color="purple"))
                + Text(
                    " ─ ",
                    style=Style(dim=True, color="yellow", bold=True),
                )
                + Text("新增", style=Style(color="green")),
                style="bright_blue",
            )
        )
        app_name = Prompt.ask("應用程式")
        acc = Prompt.ask("帳號")
        pwd = Prompt.ask("密碼")
        usernote = Prompt.ask("筆記(usernote)")
        #
        key_style = Style(color="bright_blue")
        value_style = Style(color="bright_yellow")
        tree = Tree(app_name, style=key_style)
        tree.add("帳號：", style=key_style).add(acc, style=value_style)
        tree.add("密碼：", style=key_style).add(pwd, style=value_style)
        tree.add("筆記：", style=key_style).add(
            usernote, style=value_style
        )
        self.console.print(tree)
        if Confirm.ask("是否正確： ", console=self.console) is True:
            self.data_backend.insert_data(
                app_name, acc, pwd, usernote=usernote
            )
            self.logger.info(
                f"新增：應用程式「{app_name}」、帳號「{acc}」、密碼「{pwd}」、筆記「{usernote}」。"
            )
            self.backend_save_data()
            self.get_backend_data()
            self.backend_save_data()
        else:
            self.logger.info("已取消新增")
            # self.console.print("已取消新增！")
            # time.sleep(1.5)

    def delete_appdata(self):  # TODO 新增`trash_can`垃圾桶功能
        self.console.clear()
        self.console.print(
            Rule(
                Text(project_name, style=Style(color="purple"))
                + Text(
                    " ─ ",
                    style=Style(dim=True, color="yellow", bold=True),
                )
                + Text("刪除", style=Style(color="green")),
                style="bright_blue",
            )
        )
        apps = [i for i in list(self.data.keys()) if i != "trash_can"]
        self.logger.debug(f"找到的應用程式： {apps}")
        # self.console.print(apps)
        apps_choices = Text(
            f"〔{', '.join(apps)}〕",
            style=Style(color="bright_magenta"),
        )
        while True:
            app = Prompt.ask(
                Text("選擇要刪除帳號的應用程式") + apps_choices,
                console=self.console,
            )
            if app not in apps:
                self.console.print(
                    Text(
                        f"輸入錯誤：找不到「{app}」",
                        style=Style(color="red", blink=True),
                    )
                )
            else:
                break
        #
        accs = [i["acc"] for i in self.data[app]]
        self.logger.debug(f"找到的帳號： {apps}")
        accs_choices = Text(
            f"〔{', '.join(accs)}〕",
            style=Style(color="bright_magenta"),
        )
        while True:
            acc = Prompt.ask(
                Text("選擇要刪除的帳號") + accs_choices,
                console=self.console,
            )
            if acc not in accs:
                self.console.print(
                    Text(
                        f"輸入錯誤：找不到「{acc}」",
                        style=Style(color="red", blink=True),
                    )
                )
            else:
                break
        self.console.print(self.acc_tree(app, acc))
        if Confirm.ask("是否要刪除？") is True:
            self.data_backend.delete_data(app, acc)
            self.get_backend_data()
            self.logger.info(f"已刪除應用程式「{app}」的帳號「{acc}」。")
            self.console.print("已完成刪除。")
            time.sleep(1)
        else:
            self.console.print("已取消刪除！")
            time.sleep(1)

    def acc_tree(
        self, app: str, acc: str | None = None
    ) -> Tree:  # TODO: 支援顯示`trash_can`內的內容
        ArgType("app", app, [str])
        ArgType("acc", acc, [str, None])
        #
        var_app_data: list[tuple[str, str, str, str]] = []
        if acc is None:
            if app != "trash_can" and app in list(self.data.keys()):
                for i in self.data[app]:
                    var_app_data.append(
                        (i["acc"], i["pwd"], i["note"], i["usernote"])
                    )
                    break
            else:
                msg = "找不到應用程式/帳號"
                self.logger.error(msg, stack_info=True)
                raise KeyError(msg)
        else:
            for i in self.data[app]:
                if i["acc"] == acc:
                    var_acc = i["acc"]
                    if "pwd" in i:
                        pwd = i["pwd"]
                    else:
                        pwd = ""
                        i["pwd"] = ""
                    if hasattr(i, "note") is True:
                        note = i["note"]
                    else:
                        note = ""
                    if hasattr(i, "usernote") is True:
                        usernote = i["usernote"]
                    else:
                        usernote = ""
                    var_app_data.append((var_acc, pwd, note, usernote))
                    break
            else:
                raise KeyError("找不到應用程式/帳號")
        #
        key_style = Style(color="blue")
        value_style = Style(color="yellow")
        tree = Tree(
            Text("應用程式：", style=key_style)
            + Text(app, style=value_style)
        )
        for acc, pwd, note, usernote in var_app_data:
            if self.setting["acc_tree__tree_type"] == "same_line":
                tree_acc = tree.add(
                    Text("帳號：", style=key_style)
                    + Text(acc, style=value_style)
                )
                tree_acc.add(
                    Text("密碼：", style=key_style)
                    + Text(pwd, style=value_style)
                )
                tree_acc.add(
                    Text("紀錄：", style=key_style)
                    + Text(note, style=value_style)
                )
                tree_acc.add(
                    Text("筆記：", style=key_style)
                    + Text(usernote, style=value_style)
                )
            elif (
                self.setting["acc_tree__tree_type"] == "new_line"
                or self.setting["acc_tree__tree_type"] == "old_style"
            ):
                tree_acc_key = tree.add("帳號", style=key_style)
                tree_acc_value = tree_acc_key.add(acc, style=value_style)
                tree_acc_value.add("密碼", style=key_style).add(
                    pwd, style=value_style
                )
        return tree

    def about_page(self) -> None:
        self.console.clear()
        verion_info = Text(f"版本：{self.version}")
        rule = Rule(style=Style(color="green", dim=True))
        licnese_text = Text(
            "本專案使用AGPL-3.0，LICENSE檔案：https://github.com/TW0hank0/positive_password_book/blob/master/LICENSE",
            style=Style(link=license_file_path),
        )
        author_text = Text(
            "專案作者：https://github.com/TW0hank0",
            style=Style(link="https://github.com/TW0hank0"),
        )
        project_repo = Text(
            "專案Github Repo：https://github.com/TW0hank0/positive_password_book",
            style=Style(
                link="https://github.com/TW0hank0/positive_password_book"
            ),
        )
        contents = Renderables(
            [
                verion_info,
                rule,
                licnese_text,
                author_text,
                project_repo,
            ]
        )
        panel = Panel(
            contents,
            title=Text(
                project_name,
                style=Style(color="rgb(175, 0, 255)", bold=True),
            ),
            subtitle=Text("關於", style=Style(color="green")),
            height=self.console.height - 2,
        )
        self.console.print(panel)
        # time.sleep(1)
        # Prompt.ask("按enter返回...", console=self.console)
        self.console.input("按enter返回...")

    def next_page(self):
        if (self.page_num + 1) <= self.page_max_num:
            self.page_num += 1
        else:
            self.logger.warning(
                f"已到最後一頁！總頁數：{self.page_max_num}"
            )

    def last_page(self):
        if (self.page_num - 1) >= 1:
            self.page_num -= 1
        else:
            self.logger.warning("已是第一頁！")

    def advance_save(self):
        self.console.clear()
        options = ["不加密儲存", "加密儲存"]
        options_alias = options.copy()
        options_alias.extend(["nesave", "esave"])
        for option in options:
            self.console.print(f"● {option}")
        user_option = Prompt.ask("選擇一種儲存方式", choices=options_alias)
        if user_option in ["不加密儲存", "nesave"]:
            self.data_backend.save_to_no_encrypt()
            self.data_backend.is_encrypt = False
            self.logger.info("（未加密）已儲存。")
        elif user_option in ["加密儲存", "esave"]:
            encrypt_password = Prompt.ask(
                "(不顯示) (quit退出) 加密密碼", password=True
            )
            if encrypt_password == "quit":
                self.logger.info("使用者已取消儲存。")
            else:
                retype_encrypt_password = Prompt.ask(
                    "(不顯示) (quit退出) 再次輸入加密密碼", password=True
                )
                if retype_encrypt_password == "quit":
                    self.logger.info("使用者已取消儲存。")
                else:
                    if encrypt_password == retype_encrypt_password:
                        self.data_backend.save_to_encrypt(encrypt_password)
                        self.data_backend.is_encrypt = True
                        self.data_backend.encrypt_password = (
                            encrypt_password
                        )
                        self.logger.info("已加密儲存！")
                    else:
                        self.logger.info(
                            "密碼輸入錯誤：第1次和第2次輸入不同！"
                        )

    def main(self):
        self.console.print(
            "\n" * self.console.size.height
        )  # 防止覆蓋之前的內容
        is_user_input_error = False
        # actions_old: dict[
        #     str,
        #     dict[
        #         Union[str, Literal["alias", "call"]],
        #         Union[list[str], Callable],
        #     ],
        # ] = {
        #     "新增": {"alias": ["add", "a"], "call": self.insert_appdata},
        #     "刪除": {
        #         "alias": [
        #             "delete",
        #             "d",
        #         ],
        #         "call": self.delete_appdata,
        #     },
        #     "離開": {
        #         "alias": [
        #             "quit",
        #             "q",
        #         ]
        #     },
        #     "重新整理": {
        #         "alias": [
        #             "refresh",
        #             "r",
        #         ],
        #         "call": self._main_refresh,
        #     },
        #     "關於": {
        #         "alias": [
        #             "about",
        #         ],
        #         "call": self.about_page,
        #     },
        #     "下一頁": {
        #         "alias": [
        #             "next",
        #             "n",
        #         ],
        #         "call": self._main_next_page,
        #     },
        #     "上一頁": {
        #         "alias": [
        #             "last",
        #             "l",
        #         ],
        #         "call": self._main_last_page,
        #     },
        #     "儲存": {
        #         "alias": [
        #             "save",
        #         ],
        #         "call": self._main_save,
        #     },
        #     "進階儲存": {
        #         "alias": ["advance-save", "asave"],
        #         "call": self.advance_save,
        #     },
        # }
        actions: list[PPBTUIAction] = [
            PPBTUIAction("新增", ["add", "a"], self.insert_appdata),
            PPBTUIAction(
                "刪除",
                [
                    "delete",
                    "d",
                ],
                self.delete_appdata,
            ),
            PPBTUIAction(
                "離開",
                [
                    "quit",
                    "q",
                ],
            ),
            PPBTUIAction(
                "重新整理",
                [
                    "refresh",
                    "r",
                ],
                self._main_refresh,
            ),
            PPBTUIAction(
                "關於",
                [
                    "about",
                ],
                self.about_page,
            ),
            PPBTUIAction(
                "下一頁",
                [
                    "next",
                    "n",
                ],
                self._main_next_page,
            ),
            PPBTUIAction(
                "上一頁",
                [
                    "last",
                    "l",
                ],
                self._main_last_page,
            ),
            PPBTUIAction(
                "儲存",
                [
                    "save",
                ],
                self._main_save,
            ),
            PPBTUIAction(
                "進階儲存",
                ["advance-save", "asave"],
                self.advance_save,
            ),
        ]
        all_actions = []
        for action in actions:
            all_actions.append(action.name)
            all_actions.extend(action.alias)
        self.console.clear()
        while True:
            while True:
                self.console.clear()
                self.print_data()
                if is_user_input_error is True:
                    self.console.print(
                        "輸入錯誤：請選擇一個有效的動作！",
                        style=Style(
                            underline=True, color="red", bold=True
                        ),
                    )
                    is_user_input_error = False
                prompt = Text("輸入動作") + Text(
                    f"〔{', '.join([action.name for action in actions])}〕",
                    style=Style(color="bright_magenta"),
                )
                try:
                    user_action = PPBActionPrompt.ask(
                        prompt=prompt,
                        console=self.console,
                        show_choices=False,
                    )
                except ValueError:
                    is_user_input_error = True
                    self.logger.warning("輸入錯誤：請選擇一個有效的動作！")
                else:
                    self.logger.debug(f"使用者輸入：「{user_action}」")
                    break
            if user_action not in all_actions:
                is_user_input_error = True
                self.logger.warning("輸入錯誤：請選擇一個有效的動作！")
            else:
                if user_action in ["離開", "quit", "q"]:
                    break
                elif user_action in ["重新整理", "refresh", "r"]:
                    self.get_backend_data()
                    self.refresh_page()
                elif user_action in ["關於", "about"]:
                    self.about_page()
                elif user_action in ["下一頁", "next", "n"]:
                    self.next_page()
                elif user_action in ["上一頁", "last", "l"]:
                    self.last_page()
                elif user_action in ["儲存", "save"]:
                    self.backend_save_data()
                    self.logger.info(
                        f"已儲存到檔案：「{self.data_file_path}」"
                    )
                else:
                    for action in actions:
                        if (
                            user_action == action.name
                            or user_action in action.alias
                        ):
                            act_call = action.call
                            if isinstance(act_call, Callable):
                                act_call()
                                break
                            else:
                                is_user_input_error = True
                                self.logger.warning("錯誤/unknown-err")
                    else:
                        is_user_input_error = True
                        self.logger.warning(
                            "輸入錯誤：請選擇一個有效的動作！"
                        )
        self.close()

    def _main_refresh(self):
        self.get_backend_data()
        self.refresh_page()
        self.logger.info("已重新整理。")

    def _main_save(self):
        self.backend_save_data()
        self.logger.info(f"已儲存到檔案：「{self.data_file_path}」。")

    def _main_next_page(self):
        self.next_page()
        self.logger.info(
            f"已切換到下一頁 ({self.page_num} / {self.page_max_num}) 。"
        )

    def _main_last_page(self):
        self.last_page()
        self.logger.info(
            f"已切換到上一頁 ({self.page_num} / {self.page_max_num}) 。"
        )

    def __str__(self) -> str:
        return f"""
PasswordBook
    .pages={self.pages},
    .page_num={self.page_num},
    .page_max_num={self.page_max_num},
    .content_per_page={self.content_per_page},
    .data={self.data},
    .data_file_path={self.data_file_path},
    .data_backend={self.data_backend}
"""

    def __repr__(self) -> str:
        return f"""
PasswordBook
    .pages={self.pages},
    .page_num={self.page_num},
    .page_max_num={self.page_max_num},
    .content_per_page={self.content_per_page},
    .data={self.data},
    .data_file_path={self.data_file_path},
    .data_backend={self.data_backend}
"""


def main(logger, version):
    PasswordBook(logger, version)


def launch():
    import datetime
    import os

    log_dir = os.path.join(project_path, ".logs")
    if os.path.exists(log_dir) is False or os.path.isdir(log_dir) is False:
        os.mkdir(log_dir)
    time_now = datetime.datetime.now()
    time_format_str = time_now.strftime("%Y-%d-%m_%H-%M-%S")
    log_file_path = os.path.join(log_dir, f"log_{time_format_str}.log")
    logger = pt.build_logger(log_file_path, f"{project_name}_logger")
    main(logger, project_infos.project_version)


if __name__ == "__main__":
    launch()
