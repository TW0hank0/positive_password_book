import os
import json
import sys
import logging
import datetime

from typing import Literal, Optional

import typer

import rich

from positive_tool import pt, verify

from ..project_infos import project_infos
from ..ppb_backend import ppb_backend

app_cli = typer.Typer()


def main(logger: logging.Logger):
    app_cli()


@app_cli.command()
def version():
    """顯示版本"""
    print(f"{project_infos.project_name} v{project_infos.project_version}")


@app_cli.command(name="list")
def list_all(
    password_data_file_path: Optional[str] = None,
    encrypt_password: Optional[str] = None,
    print_format: Literal["json"] = "json",
):
    """列出資料"""
    #
    verify.ArgType(
        "password_data_file_path", password_data_file_path, [str, None]
    )
    verify.ArgType("encrypt_password", encrypt_password, [str, None])
    verify.ArgType("print_format", print_format, Literal["json"])
    #
    if password_data_file_path is None:
        password_data_file_path = os.path.join(
            pt.find_project_path(
                project_infos.project_name,
                start_find_path=os.path.dirname(__file__),
            ),
            "password_data.json",
        )
    elif type(password_data_file_path) is str and (
        os.path.exists(password_data_file_path) is False
        or os.path.isfile(password_data_file_path)
    ):
        print(f"資料檔案不存在：{password_data_file_path}")
    #
    if ppb_backend.get_is_file_encrypt(password_data_file_path) is True:
        if encrypt_password is None:
            print("需要密碼！")
            sys.exit()
        else:
            backend = ppb_backend.PasswordBookSystem.load_encrypt(
                password_data_file_path, encrypt_password
            )
    else:
        backend = ppb_backend.PasswordBookSystem.password_book_load(
            password_data_file_path
        )
    #
    data = backend.password_book_get_data()
    match print_format:
        case "json":
            rich.print_json(json.dumps(data))
        case _:
            print("未知錯誤！")


if __name__ == "__main__":
    log_dir = os.path.join(project_infos.project_path, ".logs")
    if not os.path.exists(log_dir):
        os.makedirs(log_dir, exist_ok=True)
    time_now = datetime.datetime.now()
    time_format_str = time_now.strftime("%Y-%d-%m_%H-%M-%S")
    log_file_path = os.path.join(log_dir, f"log_{time_format_str}.log")
    logger = pt.build_logger(
        log_file_path, f"{project_infos.project_name}_logger"
    )
    main(logger)
