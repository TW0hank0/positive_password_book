import json
import secrets
import base64

from typing import Literal, Self, Union, Optional

from cryptography.hazmat.primitives.ciphers.aead import AESGCM
from cryptography.hazmat.primitives.kdf.scrypt import Scrypt

from positive_tool.verify import ArgType
from positive_tool import pt

from ..ppb_errors import error_backend

data_type = dict[
    str,
    list[
        dict[
            Union[
                Literal[
                    "acc",
                    "pwd",
                    "note",
                    "usernote",
                    "email",
                    "recovery-code",
                ],
                str,
            ],
            str,
        ]
    ],
]

file_content_type = dict[
    Literal["is_encrypt", "data", "encrypt_data"],
    Union[bool, data_type, str],
]


class PasswordBookSystem:
    _data: data_type

    def __init__(
        self,
        data: data_type,
        is_encrypt: bool = False,
        encrypt_password: str | None = None,
    ) -> None:
        ArgType("data", data, [dict])
        ArgType("is_encrypt", is_encrypt, [bool])
        ArgType("encrypt_password", encrypt_password, [str, None])
        self._data = data
        self._is_encrypt: bool = is_encrypt
        self._encrypt_password: str | None = encrypt_password

    @classmethod
    def password_book_new(
        cls, is_encrypt: bool = False, encrypt_password: str | None = None
    ) -> Self:
        return cls({"trash_can": []}, is_encrypt, encrypt_password)

    @classmethod
    def password_book_load(cls, file_path: str) -> Self:
        ArgType("file_path", file_path, str, is_exists=True, is_file=True)
        #
        with open(file_path, "r", encoding="utf-8") as f:
            file_data: dict = json.load(f)
        if type(file_data) is not dict:
            raise error_backend.FileContentError("資料類型錯誤！")
        else:
            return cls(file_data)

    @classmethod
    def load_encrypt(cls, file_path: str, encrypt_password: str):
        ArgType(
            "file_path", file_path, [str], is_exists=True, is_file=True
        )
        ArgType("encrypt_password", encrypt_password, [str])
        #
        with open(file_path, "r", encoding="utf-8") as f:
            file_data: file_content_type = json.load(f)
        if type(file_data["encrypt_data"]) is str:
            data_bytes = decrypt_data(
                base64.b64decode(file_data["encrypt_data"]),
                encrypt_password,
            )
            if type(data_bytes) is bytes:
                return cls(
                    json.loads(data_bytes.decode("utf-8")),
                    is_encrypt=True,
                    encrypt_password=encrypt_password,
                )
        else:
            pass
            # TODO

    def password_book_save(self, file_path: str):
        if self._data is None:
            raise error_backend.BackendSaveError("儲存失敗：資料為None")
        else:
            with open(file_path, "w", encoding="utf-8") as f:
                json.dump(
                    self._data,
                    f,
                    ensure_ascii=False,
                    indent=4,
                    sort_keys=True,
                )

    def save_encrypt(self, file_path: str, encrypt_password: str):
        if self._data is None:
            raise error_backend.BackendSaveError("儲存失敗：資料為None")
        else:
            encrypt_data = base64.b64encode(
                self.encrypt_data(
                    json.dumps(self._data).encode("utf-8"),
                    encrypt_password,
                )
            ).decode("utf-8")
            file_data: file_content_type = {
                "is_encrypt": True,
                "encrypt_data": encrypt_data,
            }
            with open(file_path, "w", encoding="utf-8") as f:
                json.dump(
                    file_data,
                    f,
                    ensure_ascii=False,
                    indent=4,
                    sort_keys=True,
                )

    def password_book_insert(
        self,
        app_name: str,
        acc: str,
        pwd: str,
        *,
        note: str = "",
        user_note: str = "",
    ):
        #
        ArgType("app_name", app_name, str)
        ArgType("acc", acc, str)
        ArgType("pwd", pwd, str)
        ArgType("note", note, str)
        ArgType("user_note", user_note, str)
        # if self._data is None:
        #     raise TypeError()
        #
        app_data = {
            "acc": acc,
            "pwd": pwd,
            "note": note,
            "user_note": user_note,
        }
        for i in list(self._data.keys()):
            if app_name == i:
                app_exists = True
                break
        else:
            app_exists: bool = False
        if app_exists is True:
            self._data[app_name].append(app_data)
        else:
            self._data[app_name] = [app_data]

    def password_book_delete(self, app_name: str, acc: str) -> None:
        #
        ArgType("app_name", app_name, str)
        ArgType("acc", acc, str)
        # if self._data is None:
        #     raise TypeError()
        #
        if app_name not in self._data.keys():
            raise error_backend.BackendDeleteError(
                "錯誤：資料(app)不存在！"
            )
        else:
            index = pt.UInt(0)
            for i in self._data[app_name]:
                if acc == i["acc"]:
                    acc_exists = True
                    break
                else:
                    index += 1
            else:
                acc_exists: bool = False
            if acc_exists is True:
                del self._data[app_name][int(index)]
                if len(self._data[app_name]) <= 0:
                    del self._data[app_name]
            else:
                raise error_backend.BackendDeleteError(
                    "錯誤：資料(acc)不存在！"
                )

    def password_book_move_to_trash_can(self, app: str, acc: str):
        # TODO:finish it
        if app in list(self._data.keys()):
            for i in self._data[app]:
                if i["acc"] == acc:
                    break
            else:
                raise IndexError()  # TODO:change error kind
        else:
            raise KeyError()  # TODO:change error kind

    def password_book_get_data(self) -> dict:
        return self._data.copy()

    def password_book_search(self, app: str) -> list | None:
        # TODO:finish it
        if app != "trash_can" and app in list(self._data.keys()):
            app_datas: list = self._data[app]
            return app_datas
        else:
            return None

    def encrypt_data(self, data: bytes, password: str) -> bytes:
        # 產生salt
        salt: bytes = secrets.token_bytes(16)
        # 使用 Scrypt
        kdf = Scrypt(
            salt=salt,
            length=32,
            n=2**17,
            r=8,
            p=1,
        )
        key: bytes = kdf.derive(password.encode("utf-8"))
        # 產生隨機nonce
        nonce: bytes = secrets.token_bytes(12)
        # 使用 AES-GCM 加密
        aesgcm = AESGCM(key)
        ciphertext: bytes = aesgcm.encrypt(
            nonce, data, associated_data=None
        )
        # 回傳
        return salt + nonce + ciphertext

    def get_is_file_encrypt(self, filepath: str):
        ArgType("filepath", filepath, str, is_exists=True, is_file=True)
        #
        with open(filepath, "r", encoding="utf-8") as f:
            file_data: file_content_type = json.load(f)
        return file_data.get("is_encrypt", False)

    def get_is_encrypt(self):
        return self._is_encrypt

    def __str__(self) -> str:
        return f"""PasswordBookSystem(_data={self._data})"""


def decrypt_data(encrypted_data: bytes, password: str) -> Optional[bytes]:
    # if len(encrypted_data) < 28:  # salt(16) + nonce(12) 最小長度
    #     return None
    ######################
    # 分割資料
    salt: bytes = encrypted_data[:16]
    nonce: bytes = encrypted_data[16:28]
    ciphertext: bytes = encrypted_data[28:]
    # 使用相同 salt 和密碼重新派生金鑰
    kdf = Scrypt(
        salt=salt,
        length=32,
        n=2**17,
        r=8,
        p=1,
    )
    try:
        key: bytes = kdf.derive(password.encode("utf-8"))
    except Exception as e:
        raise error_backend.BackendEncryptError(e)  # 密碼錯誤或 KDF 失敗
    else:
        # 解密
        aesgcm = AESGCM(key)
        try:
            plaintext: bytes = aesgcm.decrypt(
                nonce, ciphertext, associated_data=None
            )
            return plaintext
        except Exception as e:
            raise error_backend.BackendEncryptError(
                e
            )  # 密鑰錯誤、nonce 錯誤、或資料被竄改
