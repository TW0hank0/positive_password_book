import os
import json
import logging
import datetime

from typing import Literal, Optional

import typer

from positive_tool import pt

from ..project_infos import project_infos
from ..ppb_backend import ppb_backend

app_cli = typer.Typer()

server_text_arg_type = dict[str, list]
"""格式
例：
{
    "actions": [
        "get_data"
    ]
}"""


def server_text(server_text_arg: server_text_arg_type):
    backend = ppb_backend.PasswordBookSystem(
        os.path.join(project_infos["project_path"], "password_data.json")
    )
    print(server_text_arg)
    for action in server_text_arg["actions"]:
        if "get_data" in action:
            print(str(backend.password_book_get_data()))


@app_cli.command()
def server(
    server_type: Literal["text"] = "text",
    server_text_arg: Optional[str] = None,
):  # TODO:待支持檔案方式
    if server_type == "text":
        if type(server_text_arg) is str:
            server_text(json.loads(server_text_arg))
        else:
            print(f"錯誤！server_text_arg錯誤類型：{type(server_text_arg)}")
    else:
        print(f"錯誤！server_type=「{server_type}」")


@app_cli.command()
def version():
    typer.echo(f"PPB version v{project_infos['version']}")


def main(logger: logging.Logger):
    app_cli()


if __name__ == "__main__":
    log_dir = os.path.join(project_infos["project_path"], ".logs")
    if not os.path.exists(log_dir):
        os.makedirs(log_dir, exist_ok=True)
    time_now = datetime.datetime.now()
    time_format_str = time_now.strftime("%Y-%d-%m_%H-%M-%S")
    log_file_path = os.path.join(log_dir, f"log_{time_format_str}.log")
    logger = pt.build_logger(
        log_file_path, f"{project_infos['project_name']}_logger"
    )
    main(logger)
