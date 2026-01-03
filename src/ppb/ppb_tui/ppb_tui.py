import json
import time
import os
import sys
import logging
import queue

from typing import List

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


from positive_tool import pt
from positive_tool.arg import ArgType

from ..ppb_backend import ppb_backend

PROJECT_NAME = "positive_password_book"


if hasattr(sys, "_MEIPASS") is True:
    # project_path = pt.find_project_path(PROJECT_NAME, os.path.dirname(sys.executable))
    project_path = os.path.dirname(sys.executable)
else:
    project_path = pt.find_project_path(PROJECT_NAME, os.path.dirname(__file__))
# project_path = pt.find_project_path(PROJECT_NAME)


class PPBActionPrompt(PromptBase[str]):
    def __init__(
        self,
        prompt: str | Text = "",
        *,
        console: Console | None = None,
        password: bool = False,
        choices: List[str] | None = ["新增", "刪除", "離開"],
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
        # self.choice: list[str] = ["新增", "刪除", "離開"]

    def process_response(self, value: str) -> str:
        if value in self.choices or value in ["debug"]:  # type: ignore
            return value
        else:
            raise ValueError(f"在{len(self.choices)}個動作中選擇一個動作！")  # type: ignore

    def check_choice(self, value: str) -> bool:
        return value in self.choices  # type: ignore


class PPBLogHandler(logging.Handler):
    """專為Rich Console設計的Log Handler"""

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
        # renderables = Renderables()
        renderables_list = []
        # 只顯示最新的10條日誌
        recent_logs = self.logs[-10:] if len(self.logs) > 10 else self.logs
        for log in recent_logs:
            # 根據日誌等級設置顏色
            if "ERROR" in log or "CRITICAL" in log:
                log_text = Text(log, style=Style(color="red"))
            elif "WARNING" in log:
                log_text = Text(log, style=Style(color="yellow"))
            elif "DEBUG" in log:
                log_text = Text(log, style=Style(color="blue"))
            else:
                log_text = Text(log, style=Style(color="white"))
            renderables_list.append(log_text)
        renderables_list.reverse()
        return Renderables(renderables_list)

    def get_logs(self) -> list:
        """獲取所有日誌（保持原有方法兼容）"""
        return self.logs.copy()


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
        self.data_file_path = os.path.abspath(
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
        self.setting = {}
        self.setting_init_dict = {}
        self.setting_file_path = os.path.abspath(
            os.path.join(project_path, "setting_tui.json")
        )
        self.setting_init()
        self.left_change_unsave: bool = False
        self.content_per_page = self.console.size.height - 8 - 3
        self.page_num = 0
        self.page_max_num = 0
        #
        self.get_backend_data()
        self.refresh_page()
        #
        self.main()

    def setting_load(self):
        with open(self.setting_file_path, "r", encoding="utf-8") as f:
            setting_file = json.load(f)
        self.setting.update(setting_file)

    def setting_init(self):
        self.setting_init_dict["acc_tree__tree_type"] = "same_line"
        if os.path.exists(self.setting_file_path) is True and os.path.isfile(
            self.setting_file_path
        ):
            self.setting_load()
        else:
            self.setting.update(self.setting_init_dict)
            self.setting_save()

    def setting_save(self):
        with open(self.setting_file_path, "w", encoding="utf-8") as f:
            json.dump(self.setting, f, ensure_ascii=False, sort_keys=True)

    def get_backend_data(self):
        # if self.data is None:
        # self.backend.password_book_new()
        self.data = self.backend.password_book_get_data()
        self.refresh_page()

    def backend_save_data(self):
        self.backend.password_book_save(self.data_file_path)

    def print_data_old2(self):
        self.console.clear()
        if self.data is None:
            self.get_backend_data()
        # data = self.backend.password_book_get_data()
        table = Table()
        header_style = Style(color="blue")
        table.add_column("應用程式", min_width=15, header_style=header_style)
        table.add_column("帳號", min_width=20, header_style=header_style)
        table.add_column("密碼", min_width=20, header_style=header_style)
        table.add_column("user_note", header_style=header_style, min_width=10)
        table.add_column("note", header_style=header_style, min_width=10)
        for app, app_datas in list(self.data.items()):  # type: ignore
            if app == "trash_can":
                continue
            else:
                for app_data in app_datas:
                    table.add_row(app, app_data["acc"], app_data["pwd"])
        self.console.print(
            Panel(
                table,
                title=Text(PROJECT_NAME, style=Style(color="purple", bold=True)),
                height=self.console.size.height - 3,
            )
        )

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
                title=Text(PROJECT_NAME, style=Style(color="purple", bold=True)),
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
        # table = Table()
        # header_style = Style(color="blue")
        # table.add_column("應用程式", min_width=10, header_style=header_style)
        # table.add_column("帳號", min_width=20, header_style=header_style)
        # table.add_column("密碼", min_width=20, header_style=header_style)
        # table.add_column("user_note", header_style=header_style, min_width=10)
        # table.add_column("note", header_style=header_style, min_width=10)
        #
        page_info = Text(f"第{self.page_num}頁，共{self.page_max_num}頁", style=Style())
        version_text = f"版本： {self.version}"
        # version_info = Text(
        #     (
        #         " "
        #         * (
        #             int(
        #                 (
        #                     self.console.size.width
        #                     - 4
        #                     - (len(str(page_info)) + 5)
        #                     - (len(version_text) + 3)
        #                 )
        #                 / 2
        #             )
        #             - int((len(version_text) + 3) / 2)
        #         )
        #     )
        #     + version_text
        # )
        version_info = Text(version_text, justify="center")
        # self.console.print(version_info)
        info_rule = Rule(style=Style(color="green", dim=True))
        infos = Renderables([page_info])
        #
        if len(self.pages) > 0 and self.page_max_num > 0:
            tree = Tree("資料", style=Style(color="bright_blue", bold=True))
            app_rounded = []
            for app, app_data in self.pages[self.page_num - 1]:
                self.logger.debug(f"app:{app}, app_data:{app_data}")
                if app == "trash_can" or app in app_rounded:
                    continue
                else:
                    # table.add_row(app, app_data["acc"], app_data["pwd"])
                    child_tree = self.acc_tree(app)
                    self.logger.debug(f"child_tree： {child_tree}")
                    tree.children.append(child_tree)
                    app_rounded.append(app)
            content = Renderables([infos, info_rule, tree])
        else:
            content = Renderables(
                [infos, info_rule, Text("無資料", style=Style(italic=True))]
            )
        # log_panel_width = int(self.console.size.width / 3)
        log_panel_width = 25
        # content_panel_width = (log_panel_width * 2) + (
        #     (self.console.size.width - 4) - (log_panel_width * 2)
        # )
        content_panel_width = self.console.width - 25
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
            title="日志",
            width=log_panel_width,
            height=self.console.size.height - 7,
            # width=int((self.console.size.width - 4) / 3),
            # height=15,  # 設定固定高度
        )
        i = Layout(size=log_panel_width)
        i.split_row(log_panel)
        layout.add_split(i)
        all_contents = Renderables([version_info, layout])
        self.console.print(
            Panel(
                all_contents,
                title=Text(
                    PROJECT_NAME, style=Style(color="rgb(175, 0, 255)", bold=True)
                ),
                height=self.console.size.height - 3,
            )
        )

    def refresh_page(self):
        if self.data is None:
            self.get_backend_data()
        #
        self.logger.debug(f"每頁內容數： {self.content_per_page}")
        self.logger.debug(f"資料： {self.data}")
        self.logger.debug(f"資料keys： {list(self.data.keys())}")
        #
        self.pages.clear()
        # self.page_num = 1
        # self.page_max_num = 0
        count = 1
        page: list = []
        for app in list(self.data.keys()):
            self.logger.debug(f"key -> app： {app}")
            app_datas = self.data[app]
            self.logger.debug(f"value -> app_datas： {app_datas}")
            for app_data in app_datas:
                page.append((app, app_data))
                self.logger.debug(f"page： {page}")
                if count >= self.content_per_page:
                    self.pages.append(page.copy())
                    self.logger.debug(f"pages -> self.pages： {self.pages}")
                    page.clear()
                    count = 1
                else:
                    count += 1
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
                Text(PROJECT_NAME, style=Style(color="purple"))
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
                Text(PROJECT_NAME, style=Style(color="purple"))
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
        var_app_data: list[tuple[str, str]] = []
        if acc is None:
            if app != "trash_can" and app in list(self.data.keys()):
                for i in self.data:
                    if i == app:
                        for a in self.data[app]:
                            var_app_data.append((a["acc"], a["pwd"]))
                        break
                else:
                    raise KeyError("找不到應用程式/帳號")
            else:
                raise KeyError("找不到應用程式/帳號")
        else:
            for i in self.data[app]:
                if i["acc"] == acc:
                    var_app_data.append((i["acc"], i["pwd"]))
                    break
            else:
                raise KeyError("找不到應用程式/帳號")
        #
        key_style = Style(color="blue")
        value_style = Style(color="yellow")
        tree = Tree(Text("應用程式：", style=key_style) + Text(app, style=value_style))
        for acc, pwd in var_app_data:
            if self.setting["acc_tree__tree_type"] == "same_line":
                tree_acc = tree.add(
                    Text("帳號：", style=key_style) + Text(acc, style=value_style)
                )
                tree_acc.add(
                    Text("密碼：", style=key_style) + Text(pwd, style=value_style)
                )
            else:
                tree_acc_key = tree.add("帳號", style=key_style)
                tree_acc_value = tree_acc_key.add(acc, style=value_style)
                tree_acc_value.add("密碼", style=key_style).add(pwd, style=value_style)
        return tree
        #
        # if acc is not None:
        #     if (
        #         app != "trash_can"
        #         and app in list(self.data.keys())
        #         and acc in [i["acc"] for i in self.data[app]]
        #     ):
        #         key_style = Style(color="blue")
        #         value_style = Style(color="yellow")
        #         tree = Tree(app, style=key_style)
        #         if self.setting["acc_tree__tree_type"] == "same_line":
        #             tree_acc = tree.add(
        #                 Text("帳號：", style=key_style) + Text(acc, style=value_style)
        #             )
        #             for i in self.data[app]:
        #                 if i["acc"] == acc:
        #                     tree_acc.add(
        #                         Text("密碼：", style=key_style)
        #                         + Text(i["pwd"], style=value_style)
        #                     )
        #                     break
        #         else:
        #             tree_acc_key = tree.add("帳號", style=key_style)
        #             tree_acc_value = tree_acc_key.add(acc, style=value_style)
        #             for i in self.data[app]:
        #                 if i["acc"] == acc:
        #                     tree_acc_value.add("密碼", style=key_style).add(
        #                         i["pwd"], style=value_style
        #                     )
        #                     break
        #         return tree
        #     else:
        #         raise KeyError("找不到應用程式/帳號")
        # else:
        #     if app in list(self.data.keys()):
        #         key_style = Style(color="blue")
        #         value_style = Style(color="yellow")
        #         tree = Tree(app, style=key_style)
        #         app_datas = self.data[app]
        #         for app_data in app_datas:
        #             if self.setting["acc_tree__tree_type"] == "same_line":
        #                 tree_acc = tree.add(
        #                     Text("帳號：", style=key_style)
        #                     + Text(app_data["acc"], style=value_style)
        #                 )
        #                 tree_acc.add(
        #                     Text("密碼：", style=key_style)
        #                     + Text(app_data["pwd"], style=value_style)
        #                 )
        #             else:
        #                 tree_acc_key = tree.add("帳號", style=key_style)
        #                 tree_acc_value = tree_acc_key.add(
        #                     app_data["acc"], style=value_style
        #                 )
        #                 tree_acc_value.add("密碼", style=key_style).add(
        #                     app_data["pwd"], style=value_style
        #                 )
        #         return tree
        #     else:
        #         raise KeyError("找不到應用程式！")

    def main(self):
        is_user_input_error = False
        self.console.clear()
        while True:
            while True:
                self.console.clear()
                self.print_data()
                if is_user_input_error is True:
                    self.console.print(
                        "輸入錯誤：請從[bold]4[/bold]個動作中選擇一個！",
                        style=Style(blink=True, underline=True, color="red"),
                    )
                    is_user_input_error = False
                # self.console.print(
                # Text("輸入動作")
                # + Text(
                # "〔新增, 刪除, 離開, 重新整理〕",
                # style=Style(color="bright_magenta"),
                # ),
                # end="",
                # )
                prompt = Text("輸入動作") + Text(
                    "〔新增, 刪除, 離開, 重新整理〕",
                    style=Style(color="bright_magenta"),
                )
                try:
                    user_action = PPBActionPrompt.ask(
                        prompt=prompt,
                        console=self.console,
                        show_choices=False,
                        choices=[
                            "新增",
                            "a",
                            "刪除",
                            "d",
                            "離開",
                            "q",
                            "重新整理",
                            "r",
                        ],
                    )
                except ValueError:
                    # self.print_data()
                    is_user_input_error = True
                else:
                    break
            if user_action in ["新增", "a"]:
                self.insert_appdata()
            elif user_action in ["刪除", "d"]:
                # self.console.print("未完成功能！")
                # time.sleep(2)
                self.delete_appdata()
            elif user_action in ["離開", "q"]:
                break
            elif user_action in ["重新整理", "r"]:
                self.get_backend_data()
                self.refresh_page()
                # self.console.print(self)
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
)
"""


def main(logger, version):
    PasswordBook(logger, version)


def launcher():
    # TODO 待改成ppb_launcher或launch_tui統一啟動
    import os
    import datetime

    from ... import ppb  # ty:ignore[unresolved-import]

    log_dir = os.path.join(project_path, ".logs")
    if os.path.exists(log_dir) is False or os.path.isdir(log_dir) is False:
        os.mkdir(log_dir)
    time_now = datetime.datetime.now()
    time_format_str = time_now.strftime("%Y-%d-%m_%H-%M-%S")
    log_file_path = os.path.join(log_dir, f"log_{time_format_str}.log")
    logger = pt.build_logger(log_file_path, f"{PROJECT_NAME}_logger")
    main(logger, ppb.__version__)


if __name__ == "__main__":
    launcher()
