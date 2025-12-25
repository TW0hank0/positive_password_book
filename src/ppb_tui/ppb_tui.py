import os
import sys
from typing import List

from rich.console import Console
from rich.panel import Panel
from rich.table import Table
from rich.style import Style
from rich.text import Text
from rich.prompt import Prompt, PromptBase
from rich.rule import Rule
from rich.layout import Layout

from positive_tool import pt

from ..ppb_backend import password_book_system

PROJECT_NAME = "positive_password_book"
project_path = pt.find_project_path(PROJECT_NAME)


class PPBActionPrompt(PromptBase[str]):
    def __init__(
        self,
        prompt: str | Text = "",
        *,
        console: Console | None = None,
        password: bool = False,
        choices: List[str] | None = None,
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
        self.choices: list = ["新增", "刪除", "離開"]

    def process_response(self, value: str) -> str:
        if value in self.choices:
            return value
        else:
            raise ValueError(f"在{len(self.choices)}個動作中選擇一個動作！")

    def check_choice(self, value: str) -> bool:
        return value in self.choices


class PasswordBook:
    def __init__(self, logger) -> None:
        self.console = Console()
        self.logger = logger
        self.backend = password_book_system.PasswordBookSystem()
        self.data: dict | None = None
        self.data_file_path = os.path.abspath(
            os.path.join(project_path, "password_data.json")
        )
        self.left_change_unsave: bool = False
        self.content_per_page = self.console.size.height - 8 - 3
        self.page_num = 1
        #
        self.get_backend_data()
        #
        self.print_data()
        self.main()

    def get_backend_data(self):
        if self.data is None:
            self.backend.password_book_new()
            self.data = self.backend.password_book_get_data()

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
        self.console.clear()
        if self.data is None:
            self.get_backend_data()
        if hasattr(self, "pages") is False:
            self.refresh()
        # data = self.backend.password_book_get_data()
        table = Table()
        header_style = Style(color="blue")
        table.add_column("應用程式", min_width=15, header_style=header_style)
        table.add_column("帳號", min_width=20, header_style=header_style)
        table.add_column("密碼", min_width=20, header_style=header_style)
        table.add_column("user_note", header_style=header_style, min_width=10)
        table.add_column("note", header_style=header_style, min_width=10)
        for app, app_data in self.pages[self.page_num - 1]:  # type: ignore
            if app == "trash_can":
                continue
            else:
                table.add_row(app, app_data["acc"], app_data["pwd"])
        layout = Layout()
        layout.add_split(Layout(table))
        layout.add_split(Layout(Text(f"第{self.page_num}頁，共{self.page_max_num}頁")))
        self.console.print(
            Panel(
                layout,
                title=Text(PROJECT_NAME, style=Style(color="purple", bold=True)),
                height=self.console.size.height - 3,
            )
        )

    def refresh(self):
        if self.data is None:
            self.get_backend_data()
        page_app_datas = []
        self.pages = []
        for app, app_datas in list(self.data.items()):  # type: ignore
            for app_data in app_datas:
                page_app_datas.append({"app": app, "app_data": app_data})
        count = 1
        page = []
        for i in page_app_datas:
            page.append(i)
            if count >= self.content_per_page:
                self.pages.append(page)
                page.clear()
                count = 1
            else:
                count += 1
        self.page_num = 1
        self.page_max_num = len(self.pages)

    def close(self):
        self.backend_save_data()
        # self.console.print(f"退出 {PROJECT_NAME}")
        sys.exit(0)

    def insert_data(self):
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
        self.backend.password_book_insert(app_name, acc, pwd)
        self.backend_save_data()
        # self.get_backend_data()

    def main(self):
        while True:
            self.print_data()
            while True:
                try:
                    user_action = PPBActionPrompt.ask(
                        "輸入動作",
                        console=self.console,
                    )
                except ValueError as e:
                    self.print_data()
                    self.console.print(
                        f"[red]輸入錯誤：[/red][bright_red] {e}[/bright_red]",
                        style=Style(blink=True, underline=True),
                    )
                else:
                    break
            if user_action == "離開":
                break
            elif user_action == "新增":
                self.insert_data()
        self.close()


def main(logger):
    PasswordBook(logger)


def launcher():
    import os
    import datetime

    log_dir = os.path.join(project_path, ".logs")
    if os.path.exists(log_dir) is False or os.path.isdir(log_dir) is False:
        os.mkdir(log_dir)
    time_now = datetime.datetime.now()
    time_format_str = time_now.strftime("%Y-%d-%m_%H-%M-%S")
    log_file_path = os.path.join(log_dir, f"log_{time_format_str}.log")
    logger = pt.build_logger(log_file_path, f"{PROJECT_NAME}_logger")
    main(logger)


if __name__ == "__main__":
    launcher()
