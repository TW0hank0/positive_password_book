from .error_ppb import PPBError


class PPBBackendError(PPBError):
    """PPB Bacend Error"""


class FileContentError(PPBBackendError):
    """檔案資料錯誤"""


class BackendSaveError(PPBBackendError):
    """儲存檔案時發生錯誤
    可能原因：
    - 資料為空(None)"""


class BackendDeleteError(PPBBackendError):
    """刪除時發生錯誤
    可能原因
    - 資料不存在"""


class BackendEncryptError(PPBBackendError):
    """加密/解密時發生錯誤"""
