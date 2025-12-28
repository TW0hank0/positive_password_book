import json
import time
import os
import sys
import logging

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
# from rich.align import Align

# from rich.padding import Padding
from rich.containers import Renderables


from positive_tool import pt

from ..ppb_backend import ppb_backend  # ty:ignore[unresolved-import]

PROJECT_NAME = "positive_password_book"
project_path = pt.find_project_path(PROJECT_NAME)


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


class PasswordBook:
    def __init__(self, logger: logging.Logger, version) -> None:
        self.console = Console()
        self.logger: logging.Logger = logger
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
        self.left_change_unsave: bool = False
        self.content_per_page = self.console.size.height - 8 - 3
        self.page_num = 0
        self.page_max_num = 0
        #
        self.get_backend_data()
        self.refresh_page()
        #
        self.print_data()
        self.main()

    def get_backend_data(self):
        # if self.data is None:
        # self.backend.password_book_new()
        self.data = self.backend.password_book_get_data()
        self.refresh_page()

    def backend_save_data(self):
        self.backend.password_book_save(self.data_file_path)

    def print_data_old(self):
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

    def print_data(self):
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
            self.backend_save_data()
            self.get_backend_data()
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
            self.console.print("已完成刪除。")
            time.sleep(1)
        else:
            self.console.print("已取消刪除！")
            time.sleep(1)

    def acc_tree(self, app, acc) -> Tree:
        if app in list(self.data.keys()) and acc in [i["acc"] for i in self.data[app]]:
            key_style = Style(color="blue")
            value_style = Style(color="yellow")
            tree = Tree(app, style=key_style)
            tree.add("帳號", style=key_style).add(acc, style=value_style)
            for i in self.data[app]:
                if i["acc"] == acc:
                    tree.add("密碼", style=key_style).add(i["pwd"], style=value_style)
                    break
            return tree
        else:
            raise KeyError("找不到應用程式/帳號")

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
    import os
    import datetime

    from ... import positive_password_book  # ty:ignore[unresolved-import]

    log_dir = os.path.join(project_path, ".logs")
    if os.path.exists(log_dir) is False or os.path.isdir(log_dir) is False:
        os.mkdir(log_dir)
    time_now = datetime.datetime.now()
    time_format_str = time_now.strftime("%Y-%d-%m_%H-%M-%S")
    log_file_path = os.path.join(log_dir, f"log_{time_format_str}.log")
    logger = pt.build_logger(log_file_path, f"{PROJECT_NAME}_logger")
    main(logger, positive_password_book.__version__)


if __name__ == "__main__":
    launcher()
