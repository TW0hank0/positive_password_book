import os
import datetime
import sys
import traceback

from typing import Literal

import typer

from rich.traceback import install as tb_install

from positive_tool import pt, verify

if hasattr(sys, "_MEIPASS") is False:
    sys.path.insert(
        0,
        os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..")),
    )

from ...ppb.project_infos import project_infos

tb_install(show_locals=True)
PROJECT_NAME: str = project_infos["project_name"]
project_path: str = project_infos["project_path"]
version = project_infos["version"]
app_cli = typer.Typer(name=PROJECT_NAME, pretty_exceptions_short=False)


@app_cli.command()
def main(app_mode: Literal["tui", "gui", "cli"] = "tui"):
    """PPB 啟動器"""
    #
    verify.ArgType("app_mode", app_mode, Literal["tui", "gui", "cli"])
    #
    log_dir = os.path.join(project_path, ".ppb_logs")
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
    else:
        match app_mode:
            case "gui":
                logger.info("啟動GUI...")
                from ..ppb_gui import ppb_gui

                try:
                    ppb_gui.main(logger)
                except Exception as e:
                    logger.critical(f"GUI異常關閉！錯誤訊息：「{e}」")
                    logger.critical(
                        f"GUI異常關閉！traceback：「{traceback.format_exc()}」"
                    )
                    raise e
            case "tui":
                logger.info("啟動TUI...")
                from ..ppb_tui import ppb_tui

                try:
                    ppb_tui.main(logger, version)
                except Exception as e:
                    logger.critical(f"TUI異常關閉！錯誤訊息：「{e}」")
                    logger.critical(
                        f"TUI異常關閉！traceback：「{traceback.format_exc()}」"
                    )
                    raise e
            case "cli":
                logger.info("啟動CLI...")
                from ..ppb_cli import ppb_cli

                try:
                    ppb_cli.main(logger)
                except Exception as e:
                    logger.critical(f"CLI異常關閉！錯誤訊息：「{e}」")
                    logger.critical(
                        f"CLI異常關閉！traceback：「{traceback.format_exc()}」"
                    )
                    raise e


def launch():
    app_cli()


def launch_tui():
    main("tui")


def launch_gui():
    main("gui")


if __name__ == "__main__":
    launch()
