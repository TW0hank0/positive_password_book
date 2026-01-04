import os
import datetime
import sys

# import sys
# import logging
import typer

from typing import Literal

from positive_tool import pt

if hasattr(sys, "_MEIPASS") is False:
    sys.path.insert(
        0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
    )

from ... import ppb  # ty:ignore[unresolved-import]

PROJECT_NAME = "positive_password_book"
if hasattr(sys, "_MEIPASS") is True:
    # project_path = pt.find_project_path(PROJECT_NAME, os.path.dirname(sys.executable))
    project_path = os.path.dirname(sys.executable)
else:
    project_path = pt.find_project_path(PROJECT_NAME, os.path.dirname(__file__))
app_cli = typer.Typer(name=PROJECT_NAME)


@app_cli.command()
def main(app_mode: Literal["tui", "gui"] = "tui"):
    log_dir = os.path.join(project_path, ".logs")
    if os.path.exists(log_dir) is False or os.path.isdir(log_dir) is False:
        os.mkdir(log_dir)
    time_now = datetime.datetime.now()
    time_format_str = time_now.strftime("%Y-%m-%d_%H-%M-%S")
    log_file_path = os.path.join(log_dir, f"log_{time_format_str}.log")
    logger = pt.build_logger(
        log_file_path, f"{PROJECT_NAME}_logger", log_level_console=30
    )
    if logger is None:
        raise RuntimeError("日志系統初始化失敗！")
    if app_mode == "gui":
        logger.info("啟動GUI")
        from ..ppb_gui import ppb_gui

        ppb_gui.main(logger)
    elif app_mode == "tui":
        logger.info("啟動TUI")
        from ..ppb_tui import ppb_tui

        try:
            ppb_tui.main(logger, ppb.__version__)
        except Exception as e:
            print("TUI異常關閉！")
            raise e


def launch():
    app_cli()


if __name__ == "__main__":
    launch()
