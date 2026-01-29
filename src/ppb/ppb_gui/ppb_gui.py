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
    QGroupBox,
)
from PySide6.QtCore import QObject, Qt, QPoint, QEvent
from PySide6.QtGui import (
    QIcon,
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
                width: 80px;
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
        self.close_button.setStyleSheet(
            "QPushButton:hover { background-color: gray; }"
        )

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
                event.globalPosition().toPoint()
                - self.parent_obj.geometry().topLeft()
            )
            event.accept()

    def mouseMoveEvent(self, event: QMouseEvent):
        if event.buttons() == Qt.MouseButton.LeftButton and self.drag_position:
            self.parent_obj.move(
                event.globalPosition().toPoint() - self.drag_position
            )
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
        self.parent_obj.close()  # TODO:在未儲存時詢問


class PasswordBookGui(QMainWindow):
    def __new__(cls, app: QApplication, logger: logging.Logger) -> Self:
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
            Qt.WindowType.FramelessWindowHint
            | Qt.WindowType.WindowSystemMenuHint
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
        #         border-bottom-left-radius: 4px;
        #         border-bottom-right-radius: 4px;
        #         border-left: 2px solid #ddd;
        #         border-right: 2px solid #ddd;
        #         border-bottom: 2px solid #ddd;
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
        refresh_button = QPushButton("重新整理")
        refresh_button.setBaseSize(100, 40)
        refresh_button.clicked.connect(self._refresh_data)
        top_bar_layout.addWidget(refresh_button)
        content_layout.addLayout(top_bar_layout)
        app_data_layout = QVBoxLayout()
        app_data_layout.setAlignment(Qt.AlignmentFlag.AlignTop)
        self.app_data_widget = QWidget()
        # self.app_data_widget.show()
        self.app_data_widget.setLayout(app_data_layout)
        self.app_data_scroll_area = QScrollArea()
        self.app_data_scroll_area.setAlignment(
            Qt.AlignmentFlag.AlignTop | Qt.AlignmentFlag.AlignLeft
        )
        self.app_data_scroll_area.setVerticalScrollBarPolicy(
            Qt.ScrollBarPolicy.ScrollBarAlwaysOn
        )
        self.app_data_scroll_area.setHorizontalScrollBarPolicy(
            Qt.ScrollBarPolicy.ScrollBarAlwaysOn
        )
        self.app_data_scroll_area.setWidget(self.app_data_widget)
        # self.app_data_scroll_area.setWidgetResizable(True)
        content_layout.addWidget(self.app_data_scroll_area)
        ############
        central_widget.setLayout(content_layout)
        # 添加內容區
        main_layout.addWidget(central_widget)
        # 設定主要容器
        main_container = QWidget()
        main_container.setLayout(main_layout)
        self.setCentralWidget(main_container)
        # 設定初始大小
        self.resize(1080, 720)
        self.setWindowTitle(project_infos["project_name"])
        self.title_bar.title_label.setText(project_infos["project_name"])
        self._refresh_data()

    def _refresh_data(self):
        # 清空追蹤物件列表（避免累積無效引用）
        self.data_objs.clear()
        # 從後端取得最新資料
        self.data = self.backend.password_book_get_data()
        self.logger.info(f"取得後端資料：{self.data}")
        # 建立全新內容元件與版面配置
        new_content_widget: QWidget = QWidget()
        new_layout: QVBoxLayout = QVBoxLayout()
        new_layout.setAlignment(
            Qt.AlignmentFlag.AlignTop | Qt.AlignmentFlag.AlignLeft
        )
        new_layout.setSpacing(15)  # 增加項目間距提升可讀性
        # 依資料結構建立UI元件
        for app_name in self.data:
            if app_name == "trash_can":
                continue
            for app_data in self.data[app_name]:
                acc: str = app_data.get("acc", "")
                pwd: str = app_data.get("pwd", "")

                # 水平容器：單一帳密組合
                row_layout: QHBoxLayout = QHBoxLayout()
                row_layout.setSpacing(10)

                # 應用程式名稱區塊
                app_section: QHBoxLayout = QHBoxLayout()
                app_key_label: QLabel = QLabel("<u>應用程式：</u>")
                app_value_label: QLabel = QLabel(app_name)
                app_value_label.setTextInteractionFlags(
                    Qt.TextInteractionFlag.TextSelectableByMouse
                    | Qt.TextInteractionFlag.TextSelectableByKeyboard
                )
                app_section.addWidget(app_key_label)
                app_section.addWidget(app_value_label)
                app_section.addStretch(50)

                # 帳號區塊
                acc_section: QHBoxLayout = QHBoxLayout()
                acc_key_label: QLabel = QLabel("<u>帳號：</u>")
                acc_value_label: QLabel = QLabel(acc)
                acc_value_label.setTextInteractionFlags(
                    Qt.TextInteractionFlag.TextSelectableByMouse
                    | Qt.TextInteractionFlag.TextSelectableByKeyboard
                )
                acc_section.addWidget(acc_key_label)
                acc_section.addWidget(acc_value_label)
                acc_section.addStretch(50)

                # 密碼區塊
                pwd_section: QHBoxLayout = QHBoxLayout()
                pwd_key_label: QLabel = QLabel("<u>密碼：</u>")
                pwd_value_label: QLabel = QLabel(pwd)
                pwd_value_label.setTextInteractionFlags(
                    Qt.TextInteractionFlag.TextSelectableByMouse
                    | Qt.TextInteractionFlag.TextSelectableByKeyboard
                )
                pwd_section.addWidget(pwd_key_label)
                pwd_section.addWidget(pwd_value_label)
                pwd_section.addStretch(50)
                # 組合三欄位至單一列
                row_layout.addLayout(app_section)
                row_layout.addLayout(acc_section)
                row_layout.addLayout(pwd_section)
                row_layout.addStretch()
                # 追蹤元件
                self.data_objs.extend(
                    [app_value_label, acc_value_label, pwd_value_label]
                )
                new_layout.addLayout(row_layout)
            # 應用新元件至ScrollArea
            new_content_widget.setLayout(new_layout)
            self.app_data_scroll_area.setWidget(new_content_widget)
            self.app_data_widget = new_content_widget  # 更新引用

    def changeEvent(self, event: QEvent):
        if (
            event.type() == QEvent.Type.WindowStateChange
            and self.title_bar is not None
        ):
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
    app.setWindowIcon(
        QIcon(os.path.join(project_infos["project_path"], "icon.png"))
    )
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
