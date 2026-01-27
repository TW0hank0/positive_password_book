from logging import Logger
import os
import datetime
import logging

from typing_extensions import Self

from PySide6.QtWidgets import (
    QLabel,
    QVBoxLayout,
    QHBoxLayout,
    QPushButton,
    QWidget,
    QApplication,
    QMainWindow,
    QScrollArea,
)
from PySide6.QtCore import QObject, Qt, QPoint, QEvent
from PySide6.QtGui import (
    QMouseEvent,
    QFont,
    QFontDatabase,
)
from positive_tool import pt

from ..project_infos import project_infos
from ..ppb_backend import ppb_backend

project_name = project_infos["project_name"]
project_path = project_infos["project_path"]
version = project_infos["version"]
font_noto_sans_path = os.path.normpath(
    os.path.join(
        project_path,
        "assets",
        "fonts",
        "Noto_Sans_TC",
        "static",
        "NotoSansTC-Regular.ttf",
    )
)


class CustomTitleBar(QWidget):
    def __init__(self, parent: QMainWindow):
        super().__init__(parent)
        self.setParent(parent)
        self.parent_obj = parent
        self.drag_position = QPoint()
        # 設定標題列樣式
        self.setStyleSheet("""
            QWidget {
                background-color: #2c3e50;
                border-top-left-radius: 8px;
                border-top-right-radius: 8px;
            }
            QLabel {
                color: white;
                font-weight: bold;
                padding: 5px;
            }
            QPushButton {
                background-color: transparent;
                border: none;
                color: white;
                font-weight: bold;
                width: 40px;
                height: 30px;
                border-radius: 5px;
            }
            QPushButton:hover {
                background-color: #34495e;
            }
            QPushButton:pressed {
                background-color: #1a252f;
            }
        """)

        # 標題列佈局
        layout = QHBoxLayout()
        layout.setContentsMargins(10, 5, 10, 5)
        layout.setSpacing(5)

        # 標題標籤
        self.title_label = QLabel("標題")
        self.title_label.setStyleSheet("font-size: 14px;")

        # 按鈕
        self.minimize_button = QPushButton("─")
        self.maximize_button = QPushButton("□")
        self.close_button = QPushButton("×")

        # 按鈕大小
        for btn in [
            self.minimize_button,
            self.maximize_button,
            self.close_button,
        ]:
            btn.setFixedSize(40, 30)

        # 設定按鈕樣式
        self.minimize_button.setStyleSheet(
            "QPushButton:hover { background-color: gray; }"
        )
        self.maximize_button.setStyleSheet(
            "QPushButton:hover { background-color: gray; }"
        )
        self.close_button.setStyleSheet("QPushButton:hover { background-color: gray; }")

        # 連接按鈕訊號
        self.minimize_button.clicked.connect(self.minimize_window)
        self.maximize_button.clicked.connect(self.toggle_maximize)
        self.close_button.clicked.connect(self.close_window)
        # 添加到佈局
        layout.addWidget(self.title_label)
        layout.addStretch()
        layout.addWidget(self.minimize_button)
        layout.addWidget(self.maximize_button)
        layout.addWidget(self.close_button)
        self.setLayout(layout)

    def mousePressEvent(self, event: QMouseEvent):
        if event.button() == Qt.MouseButton.LeftButton:
            self.drag_position = (
                event.globalPosition().toPoint() - self.parent_obj.geometry().topLeft()
            )
            event.accept()

    def mouseMoveEvent(self, event: QMouseEvent):
        if event.buttons() == Qt.MouseButton.LeftButton and self.drag_position:
            self.parent_obj.move(event.globalPosition().toPoint() - self.drag_position)
            event.accept()

    def minimize_window(self):
        if self.parent_obj.isMinimized() is False:
            self.parent_obj.showMinimized()

    def toggle_maximize(self):
        if self.parent_obj.isMaximized() is True:
            self.parent_obj.showNormal()
            self.maximize_button.setText("□")
        else:
            self.parent_obj.showMaximized()
            self.maximize_button.setText("❐")

    def close_window(self):
        self.parent_obj.close()  # TODO:考慮在未儲存時詢問


class PasswordBookGui(QMainWindow):
    def __new__(cls, app: QApplication, logger) -> Self:
        cls.title_bar = None
        return super().__new__(cls)

    def __init__(self, app: QApplication, logger: logging.Logger):
        super().__init__()
        self.app = app
        self.logger: logging.Logger = logger
        self.config_path = os.path.join(
            project_infos["project_path"], "password_data.json"
        )
        self.backend = ppb_backend.PasswordBookSystem(self.config_path)
        self.backend.password_book_load(self.config_path)
        self.data = {}
        self.data_objs: list[QObject] = []
        self.showMaximized()
        # 設定無框視窗
        self.setWindowFlags(
            Qt.WindowType.FramelessWindowHint | Qt.WindowType.WindowSystemMenuHint
        )
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground)
        # 字體
        font_id = QFontDatabase.addApplicationFont(font_noto_sans_path)
        if font_id != -1:
            family = QFontDatabase.applicationFontFamilies(font_id)[0]
            app_font = QFont(family, 20)
        else:
            app_font = QFont("Microsoft JhengHei", 20)  # 若載入失敗則用系統字型
        self.setFont(app_font)
        # 主要內容區
        central_widget = QWidget()
        # central_widget.setStyleSheet("""
        #     QWidget {
        #         background-color: black;
        #         border-bottom-left-radius: 8px;
        #         border-bottom-right-radius: 8px;
        #         border-left: 1px solid #ddd;
        #         border-right: 1px solid #ddd;
        #         border-bottom: 1px solid #ddd;
        #     }
        # """)
        # 主佈局
        main_layout = QVBoxLayout()
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.setSpacing(0)
        # 添加自訂標題列
        self.title_bar = CustomTitleBar(self)
        self.title_bar.setFixedHeight(50)
        self.title_bar.setGeometry(
            0,
            0,
            self.title_bar.size().width(),
            self.title_bar.size().height(),
        )
        main_layout.addWidget(self.title_bar)
        content_layout = QVBoxLayout()  # 內容佈局
        content_layout.setContentsMargins(20, 40, 20, 20)
        ############
        # 內容
        top_bar_layout = QHBoxLayout()
        top_bar_layout.setAlignment(Qt.AlignmentFlag.AlignLeft)
        project_name_text = QLabel(
            f"<font size='5'><b>{project_name}</b></font>",
            textFormat=Qt.TextFormat.RichText,
        )
        project_name_text.setAlignment(
            Qt.AlignmentFlag.AlignVCenter | Qt.AlignmentFlag.AlignLeft
        )
        version_text = QLabel(f"<font size='2'>版本：{version}</font>")
        version_text.setAlignment(
            Qt.AlignmentFlag.AlignBottom | Qt.AlignmentFlag.AlignLeft
        )
        top_bar_layout.addWidget(project_name_text)
        top_bar_layout.addWidget(version_text)
        content_layout.addLayout(top_bar_layout)
        self.app_data_layout = QVBoxLayout()
        self.app_data_layout.setAlignment(Qt.AlignmentFlag.AlignTop)
        app_data_widget = QWidget()
        app_data_widget.setLayout(self.app_data_layout)
        app_data_scroll_area = QScrollArea(parent=self)
        app_data_scroll_area.setAlignment(
            Qt.AlignmentFlag.AlignTop | Qt.AlignmentFlag.AlignLeft
        )
        app_data_scroll_area.setWidget(app_data_widget)
        app_data_scroll_area.setVerticalScrollBarPolicy(
            Qt.ScrollBarPolicy.ScrollBarAlwaysOn
        )
        app_data_scroll_area.setHorizontalScrollBarPolicy(
            Qt.ScrollBarPolicy.ScrollBarAlwaysOn
        )
        app_data_scroll_area.setWidgetResizable(True)
        content_layout.addWidget(app_data_scroll_area)
        ############
        central_widget.setLayout(content_layout)
        # 添加內容區
        main_layout.addWidget(central_widget)
        # 設定主要容器
        container = QWidget()
        container.setLayout(main_layout)
        self.setCentralWidget(container)
        # 設定初始大小
        self.resize(1080, 720)
        self.setWindowTitle(project_infos["project_name"])
        self.title_bar.title_label.setText(project_infos["project_name"])
        self._refresh_data()

    def _refresh_data(self):
        if len(self.data_objs) > 0:
            for obj in self.data_objs:
                if hasattr(obj, "hide") is True:
                    obj.hide()  # pyright: ignore[reportAttributeAccessIssue]
                obj.deleteLater()
        self.data = self.backend.password_book_get_data()
        self.logger.info(f"取得後端資料：{self.data}")
        for app_name in self.data:
            if app_name == "trash_can":
                pass
            else:
                for app_data in self.data[app_name]:
                    acc = app_data.get("acc", "")
                    pwd = app_data.get("pwd", "")
                    layout_h = QHBoxLayout()
                    layout_app_name = QHBoxLayout()
                    app_name_key = QLabel("<u>應用程式：</u>")
                    app_name_value = QLabel(
                        app_name,
                    )
                    layout_app_name.addWidget(app_name_key)
                    layout_app_name.addWidget(app_name_value)
                    app_name_value.setTextInteractionFlags(
                        Qt.TextInteractionFlag.TextSelectableByMouse
                        | Qt.TextInteractionFlag.TextSelectableByKeyboard
                    )
                    layout_acc = QHBoxLayout()
                    acc_label_key = QLabel(
                        "<u>帳號：</u>",
                    )
                    acc_label_value = QLabel(
                        acc,
                    )
                    acc_label_value.setTextInteractionFlags(
                        Qt.TextInteractionFlag.TextSelectableByMouse
                        | Qt.TextInteractionFlag.TextSelectableByKeyboard
                    )
                    layout_acc.addWidget(acc_label_key)
                    layout_acc.addWidget(acc_label_value)
                    layout_pwd = QHBoxLayout()
                    pwd_label_key = QLabel(
                        "<u>密碼：</u>",
                    )
                    pwd_label_value = QLabel(
                        pwd,
                    )
                    pwd_label_value.setTextInteractionFlags(
                        Qt.TextInteractionFlag.TextSelectableByMouse
                        | Qt.TextInteractionFlag.TextSelectableByKeyboard
                    )
                    layout_pwd.addWidget(pwd_label_key)
                    layout_pwd.addWidget(pwd_label_value)
                    layout_h.addLayout(layout_app_name)
                    layout_h.addLayout(layout_acc)
                    layout_h.addLayout(layout_pwd)
                    self.app_data_layout.addLayout(layout_h)
                    # TODO:下方
                    self.data_objs.append(app_name_value)
                    self.data_objs.append(acc)
                    self.data_objs.append(pwd)
                    self.data_objs.append(layout_h)

    def changeEvent(self, event: QEvent):
        if event.type() == QEvent.Type.WindowStateChange and self.title_bar is not None:
            if self.isMaximized():
                self.title_bar.maximize_button.setText("❐")
            else:
                self.title_bar.maximize_button.setText("□")
        super().changeEvent(event)


def main(logger):
    app = QApplication()
    # 設定應用程式樣式
    app.setStyle("Fusion")
    # 字體
    font_id = QFontDatabase.addApplicationFont(font_noto_sans_path)
    if font_id != -1:
        family = QFontDatabase.applicationFontFamilies(font_id)[0]
        app_font = QFont(family, 20)
    else:
        app_font = QFont("Microsoft JhengHei", 20)
    app.setFont(app_font)
    #
    window = PasswordBookGui(app, logger)
    window.show()
    app.exec()


if __name__ == "__main__":
    log_dir = os.path.join(project_path, ".logs")
    if os.path.exists(log_dir) is False or os.path.isdir(log_dir) is False:
        os.mkdir(log_dir)
    time_now = datetime.datetime.now()
    time_format_str = time_now.strftime("%Y-%d-%m_%H-%M-%S")
    log_file_path = os.path.join(log_dir, f"log_{time_format_str}.log")
    logger = pt.build_logger(log_file_path, f"{project_name}_logger")
    main(logger)
