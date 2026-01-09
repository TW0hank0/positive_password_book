import json
import time
import os
import sys
import logging

from typing import Literal, Any

from rich.console import Console
from rich.panel import Panel
from rich.table import Table
from rich.style import Style
from rich.text import Text
from rich.prompt import Prompt, PromptBase, Confirm
from rich.rule import Rule
from rich.layout import Layout
from rich.tree import Tree
from rich.containers import Renderables
# from rich.color import Color


from positive_tool import pt
from positive_tool.arg import ArgType

from ..ppb_backend import ppb_backend
from ...ppb.project_infos import project_infos

project_name: str = project_infos["project_name"]
license_file_path = project_infos["project_license_file_path"]
project_path = project_infos["project_path"]
# if hasattr(sys, "_MEIPASS") is True:
#     # project_path = pt.find_project_path(PROJECT_NAME, os.path.dirname(sys.executable))
#     project_path = os.path.dirname(sys.executable)
# else:
#     project_path = pt.find_project_path(project_name, os.path.dirname(__file__))


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
        # if (
        #     value is not None
        #     and type(value) is str
        #     and value in self.choices
        #     or value in ["debug"]
        # ):  # type: ignore
        #     return value
        # else:
        #     raise ValueError(f"在{len(self.choices)}個動作中選擇一個動作！")


class PPBLogHandler(logging.Handler):
    def __init__(self, console: Console, level=logging.INFO):
        super().__init__(level)
        self.console = console
        self.logs = []  # 存儲日誌的列表
        self.max_logs = 50  # 最大日誌數量
        # 設置日誌格式
        self.formatter = logging.Formatter(
            "%(asctime)s | %(levelname)s | %(message)s", datefmt="%H:%M:%S"
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
                log_text = Text(log, style=Style(color="bright_red", bold=True))
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


class PPBSetting:  # TODO: 待轉成GUI、TUI通用，移到ppb_backend
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
                self._bytes_to_mb(os.path.getsize(self.setting_file_path)) < 10
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
        if os.path.exists(self.setting_file_path) is True and os.path.isfile(
            self.setting_file_path
        ):
            self.setting_load()
        else:
            self.setting_save()

    def setting_save(self) -> None:
        with open(self.setting_file_path, "w", encoding="utf-8") as f:
            json.dump(self.data, f, ensure_ascii=False, sort_keys=True, indent=4)

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


class PasswordBook:
    def __init__(self, logger: logging.Logger, version) -> None:
        self.console = Console()
        self.logger: logging.Logger = logger
        self.ppb_tui_log_handler = PPBLogHandler(console=self.console)
        self.logger.addHandler(self.ppb_tui_log_handler)
        self.version = version
        self.backend = ppb_backend.PasswordBookSystem()
        self.data: dict = {}
        self.pages: list = []
        self.data_file_path: str = os.path.abspath(
            os.path.join(project_path, "password_data.json")
        )
        if os.path.isfile(self.data_file_path) is True:
            try:
                self.backend.password_book_load(self.data_file_path)
            except json.JSONDecodeError:
                self.console.print("檔案格式錯誤！")
                self.console.print_exception(show_locals=True)
                sys.exit(1)
        else:
            self.backend.password_book_new()
        # self.setting = {}
        # self.setting_init_dict = {}
        self.setting_file_path = os.path.abspath(
            os.path.join(project_path, "setting_tui.json")
        )
        self.setting = PPBSetting(self.setting_file_path, self.logger)
        # self.setting_init()
        self.left_change_unsave: bool = False
        self.content_per_page: int = self.console.size.height - 13
        self.page_num = 0
        self.page_max_num = 0
        #
        self.init_color()
        self.get_backend_data()
        self.refresh_page()
        #
        self.main()

    def init_color(self):
        self.colors = {}
        # tmp = {"purple": Color.from_rgb(175, 0, 255).get_ansi_codes()}
        # for i in tmp:
        #     tmp_color = ""
        #     for i2 in tmp[i]:
        #         tmp_color = tmp_color + f"\033[{i2}m"
        #     self.colors[i] = tmp_color

    # def setting_load(self):
    #     with open(self.setting_file_path, "r", encoding="utf-8") as f:
    #         setting_file = json.load(f)
    #     self.setting.update(setting_file)

    # def setting_init(self):
    #     self.setting_init_dict["acc_tree__tree_type"] = "same_line"
    #     if os.path.exists(self.setting_file_path) is True and os.path.isfile(
    #         self.setting_file_path
    #     ):
    #         self.setting_load()
    #     else:
    #         self.setting.update(self.setting_init_dict)
    #         self.setting_save()

    # def setting_save(self):
    #     with open(self.setting_file_path, "w", encoding="utf-8") as f:
    #         json.dump(self.setting, f, ensure_ascii=False, sort_keys=True)

    def get_backend_data(self):
        # if self.data is None:
        # self.backend.password_book_new()
        self.data = self.backend.password_book_get_data()
        self.refresh_page()

    def backend_save_data(self):
        self.backend.password_book_save(self.data_file_path)

    def print_data_old(self):
        #
        # self.console.clear()
        # if self.data is None:
        # self.get_backend_data()
        # if hasattr(self, "pages") is False:
        # self.refresh_page()
        #
        self.logger.debug(f"所有分頁： {self.pages}")
        self.logger.debug(f"資料： {self.data}")
        self.logger.debug(f"總頁數： {self.page_max_num}")
        #
        table = Table()
        header_style = Style(color="blue")
        table.add_column("應用程式", min_width=10, header_style=header_style)
        table.add_column("帳號", min_width=20, header_style=header_style)
        table.add_column("密碼", min_width=20, header_style=header_style)
        table.add_column("user_note", header_style=header_style, min_width=10)
        table.add_column("note", header_style=header_style, min_width=10)
        if len(self.pages) > 0 and self.page_max_num > 0:
            for app, app_data in self.pages[self.page_num - 1]:
                self.logger.debug(f"app:{app}, app_data:{app_data}")
                if app == "trash_can":
                    continue
                else:
                    table.add_row(app, app_data["acc"], app_data["pwd"])
        layout = Layout()
        layout.add_split(Layout(table))
        # layout.add_split(Layout(Text(f"第{self.page_num}頁，共{self.page_max_num}頁")))
        page_info = Text(
            f"第{self.page_num}頁，共{self.page_max_num}頁", style="", end=""
        )
        version_text = f"版本： {self.version}"
        version_info = Text(
            (
                " "
                * (
                    int(
                        (
                            self.console.size.width
                            - 4
                            - (len(str(page_info)) + 5)
                            - (len(version_text) + 3)
                        )
                        / 2
                    )
                    - int((len(version_text) + 3) / 2)
                )
            )
            + version_text
        )
        info_rule = Rule(style=Style(color="green", dim=True))
        infos = Renderables([page_info, version_info])
        content = Renderables([infos, info_rule, table])
        # 建立內容組合
        # content = Renderables(
        # [table, Align(page_info, align="right", vertical="bottom")]
        # )
        # self.console.print(
        # Panel(
        # layout,
        # title=Text(PROJECT_NAME, style=Style(color="purple", bold=True)),
        # height=self.console.size.height - 3,
        # )
        # )
        # self.console.print(Text(f"第{self.page_num}頁，共{self.page_max_num}頁"))
        self.console.print(
            Panel(
                content,
                title=Text(project_name, style=Style(color="purple", bold=True)),
                height=self.console.size.height - 3,
            )
        )

    def print_data(self, clear_scrren: bool = False):
        self.logger.debug(f"所有分頁： {self.pages}")
        self.logger.debug(f"資料： {self.data}")
        self.logger.debug(f"總頁數： {self.page_max_num}")
        #
        if clear_scrren is True:
            self.console.clear()
        page_info = Text(f"第{self.page_num}頁，共{self.page_max_num}頁", style=Style())
        version_text = f"版本：{self.version}"
        version_info = Text(version_text, justify="center")
        info_rule = Rule(style=Style(color="green", dim=True))
        infos = Renderables([page_info])
        #
        if len(self.pages) > 0 and self.page_max_num > 0:
            tree = Tree("資料", style=Style(color="bright_blue", bold=True))
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
                [infos, info_rule, Text("無資料", style=Style(italic=True))]
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
                    project_name, style=Style(color="rgb(175, 0, 255)", bold=True)
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
                    self.logger.debug(f"pages -> self.pages： {self.pages}")
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
        sys.exit(0)

    def insert_appdata(self):
        self.console.clear()
        self.console.print(
            Rule(
                Text(project_name, style=Style(color="purple"))
                + Text(" ─ ", style=Style(dim=True, color="yellow", bold=True))
                + Text("新增", style=Style(color="green")),
                style="bright_blue",
            )
        )
        app_name = Prompt.ask("應用程式")
        acc = Prompt.ask("帳號")
        pwd = Prompt.ask("密碼")
        #
        key_style = Style(color="blue")
        value_style = Style(color="yellow")
        tree = Tree(app_name, style=key_style)
        tree.add("帳號：", style=key_style).add(acc, style=value_style)
        tree.add("密碼：", style=key_style).add(pwd, style=value_style)
        # self.console.print(Text("應用程式：", style=key_style, end=""), end="\n")
        # self.console.print(Text(app_name, style=value_style, end=""), end="\n")
        # self.console.print(Text("帳號：", style=key_style))
        # self.console.print(Text(acc, style=value_style, end=""), end="\n")
        # self.console.print(Text("密碼：", style=key_style))
        # self.console.print(Text(pwd, style=value_style, end=""), end="\n")
        self.console.print(tree)
        if Confirm.ask("是否正確： ", console=self.console):
            self.backend.password_book_insert(app_name, acc, pwd)
            self.logger.info(
                f"新增：應用程式「{app_name}」、帳號「{acc}」、密碼「{pwd}」。"
            )
            self.backend_save_data()
            self.get_backend_data()
            self.backend_save_data()
        else:
            self.console.print("已取消新增！")
            time.sleep(1.5)

    def delete_appdata(self):  # TODO 新增`trash_can`垃圾桶功能
        self.console.clear()
        self.console.print(
            Rule(
                Text(project_name, style=Style(color="purple"))
                + Text(" ─ ", style=Style(dim=True, color="yellow", bold=True))
                + Text("刪除", style=Style(color="green")),
                style="bright_blue",
            )
        )
        apps = [i for i in list(self.data.keys()) if i != "trash_can"]
        self.logger.debug(f"找到的應用程式： {apps}")
        # self.console.print(apps)
        apps_choices = Text(
            f"〔{', '.join(apps)}〕", style=Style(color="bright_magenta")
        )
        while True:
            app = Prompt.ask(
                Text("選擇要刪除帳號的應用程式") + apps_choices, console=self.console
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
            f"〔{', '.join(accs)}〕", style=Style(color="bright_magenta")
        )
        while True:
            acc = Prompt.ask(
                Text("選擇要刪除的帳號") + accs_choices, console=self.console
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
            self.backend.password_book_delete(app, acc)
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
                    var_app_data.append((i["acc"], i["pwd"], i["note"], i["usernote"]))
                    break
            else:
                msg = "找不到應用程式/帳號"
                self.logger.error(msg, stack_info=True)
                raise KeyError(msg)
        else:
            for i in self.data[app]:
                if i["acc"] == acc:
                    var_acc = i["acc"]
                    pwd = i["pwd"]
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
        tree = Tree(Text("應用程式：", style=key_style) + Text(app, style=value_style))
        for acc, pwd, note, usernote in var_app_data:
            if self.setting["acc_tree__tree_type"] == "same_line":
                tree_acc = tree.add(
                    Text("帳號：", style=key_style) + Text(acc, style=value_style)
                )
                tree_acc.add(
                    Text("密碼：", style=key_style) + Text(pwd, style=value_style)
                )
                tree_acc.add(
                    Text("紀錄：", style=key_style) + Text(note, style=value_style)
                )
                tree_acc.add(
                    Text("筆記：", style=key_style) + Text(usernote, style=value_style)
                )
            elif (
                self.setting["acc_tree__tree_type"] == "new_line"
                or self.setting["acc_tree__tree_type"] == "old_style"
            ):
                tree_acc_key = tree.add("帳號", style=key_style)
                tree_acc_value = tree_acc_key.add(acc, style=value_style)
                tree_acc_value.add("密碼", style=key_style).add(pwd, style=value_style)
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
            style=Style(link="https://github.com/TW0hank0/positive_password_book"),
        )
        contents = Renderables(
            [verion_info, rule, licnese_text, author_text, project_repo]
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
            self.logger.warning(f"已到最後一頁！總頁數：{self.page_max_num}")

    def last_page(self):
        if (self.page_num - 1) >= 1:
            self.page_num -= 1
        else:
            self.logger.warning("已是第一頁！")

    def main(self):
        self.console.print("\n" * self.console.size.height)  # 防止覆蓋之前的內容
        is_user_input_error = False
        actions = [
            "新增",
            "add",
            "a",
            "刪除",
            "delete",
            "d",
            "離開",
            "quit",
            "q",
            "重新整理",
            "refresh",
            "r",
            "關於",
            "about",
            "下一頁",
            "next",
            "n",
            "上一頁",
            "last",
            "l",
        ]
        self.console.clear()
        while True:
            while True:
                self.console.clear()
                self.print_data()
                if is_user_input_error is True:
                    self.console.print(
                        "輸入錯誤：請從[bold]5[/bold]個動作中選擇一個！",
                        style=Style(blink=True, underline=True, color="red"),
                    )
                    is_user_input_error = False
                prompt = Text("輸入動作") + Text(
                    "〔新增, 刪除, 離開, 重新整理, 關於, 下一頁, 上一頁〕",
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
                    break
            if user_action not in actions:
                is_user_input_error = True
                self.logger.warning("輸入錯誤：請選擇一個有效的動作！")
            else:
                if user_action in ["新增", "add", "a"]:
                    self.insert_appdata()
                elif user_action in ["刪除", "delete", "d"]:
                    self.delete_appdata()
                elif user_action in ["離開", "quit", "q"]:
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
                else:
                    is_user_input_error = True
                    self.logger.warning("輸入錯誤：請選擇一個有效的動作！")
        self.close()

    def __str__(self) -> str:
        return f"""PasswordBook(
    pages={self.pages},
    page_num={self.page_num},
    page_max_num={self.page_max_num},
    content_per_page={self.content_per_page},
    data={self.data},
    data_file_path={self.data_file_path},
    backend={self.backend}
)"""

    def __repr__(self) -> str:
        return f"""PasswordBook(
    pages={self.pages},
    page_num={self.page_num},
    page_max_num={self.page_max_num},
    content_per_page={self.content_per_page},
    data={self.data},
    data_file_path={self.data_file_path},
    backend={self.backend}
)"""


def main(logger, version):
    PasswordBook(logger, version)


def launcher():
    # TODO:待改成ppb_launcher或launch_tui統一啟動
    import os
    import datetime

    log_dir = os.path.join(project_path, ".logs")
    if os.path.exists(log_dir) is False or os.path.isdir(log_dir) is False:
        os.mkdir(log_dir)
    time_now = datetime.datetime.now()
    time_format_str = time_now.strftime("%Y-%d-%m_%H-%M-%S")
    log_file_path = os.path.join(log_dir, f"log_{time_format_str}.log")
    logger = pt.build_logger(log_file_path, f"{project_name}_logger")
    main(logger, project_infos["version"])


if __name__ == "__main__":
    launcher()
