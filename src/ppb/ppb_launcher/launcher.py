import os
import datetime
import sys
import subprocess
import platform
import webbrowser

from traceback import print_exception
from typing import Literal

import typer

from rich.traceback import install as tb_install

from positive_tool import pt

if hasattr(sys, "_MEIPASS") is False:
    sys.path.insert(
        0,
        os.path.abspath(
            os.path.join(os.path.dirname(__file__), "..", "..")
        ),
    )

from ...ppb.project_infos import project_infos

tb_install(show_locals=True)
PROJECT_NAME: str = project_infos["project_name"]
project_path: str = project_infos["project_path"]
version = project_infos["version"]
# PROJECT_NAME = "positive_password_book"
# if hasattr(sys, "_MEIPASS") is True:
#     # project_path = pt.find_project_path(PROJECT_NAME, os.path.dirname(sys.executable))
#     project_path = os.path.dirname(sys.executable)
# else:
#     project_path = pt.find_project_path(PROJECT_NAME, os.path.dirname(__file__))
app_cli = typer.Typer(
    name=PROJECT_NAME, pretty_exceptions_short=False
)


@app_cli.command()
def main(app_mode: Literal["tui", "gui"] = "tui"):
    """PPB 啟動器"""
    log_dir = os.path.join(project_path, ".logs")
    if (
        os.path.exists(log_dir) is False
        or os.path.isdir(log_dir) is False
    ):
        os.mkdir(log_dir)
    time_now = datetime.datetime.now()
    time_format_str = time_now.strftime("%Y-%m-%d_%H-%M-%S")
    log_file_path = os.path.join(
        log_dir, f"log_{time_format_str}.log"
    )
    logger = pt.build_logger(
        log_file_path, f"{PROJECT_NAME}_logger", log_level_console=30
    )
    if logger is None:
        raise RuntimeError("日志系統初始化失敗！")
    if app_mode == "gui":
        gui_exec_dir_path = os.path.join(
            project_infos["project_path"],
            "src",
            "ppb",
            "ppb_gui",
            "exports",
        )
        exec_file_type: Literal["exec", "web"]
        match platform.platform():
            case "Windows":
                logger.info("在Windows啟動GUI。")
                gui_exec_file_path = os.path.join(
                    gui_exec_dir_path, "win", "ppb_gui_win_x86-64.exe"
                )
                exec_file_type = "exec"
            case _:
                gui_exec_file_path = os.path.join(
                    gui_exec_dir_path, "web", "ppb_gui_web"
                )
                exec_file_type = "web"
        logger.info("啟動GUI。")
        if exec_file_type == "exec":
            try:
                subprocess.run(gui_exec_file_path)
            except Exception as e:
                logger.critical(f"GUI異常關閉！錯誤訊息：「{e}」")
                print_exception(e)
        elif exec_file_type == "web":
            result = webbrowser.open(gui_exec_file_path)
            if result is not True:
                logger.critical("WEB GUI開啟失敗！")
        else:
            logger.critical(
                f"未知錯誤：exec_file_type=「{exec_file_type}」、gui_exec_file_path=「{gui_exec_file_path}」"
            )
            sys.exit(1)
    elif app_mode == "tui":
        logger.info("啟動TUI")
        from ..ppb_tui import ppb_tui

        try:
            ppb_tui.main(logger, version)
        except Exception as e:
            logger.critical(f"TUI異常關閉！錯誤訊息：「{e}」")
            raise e


def launch():
    app_cli()


def launch_tui():
    main("tui")


if __name__ == "__main__":
    launch()
