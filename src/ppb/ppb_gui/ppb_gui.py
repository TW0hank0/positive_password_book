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
from PySide6.QtCore import Qt, QPoint, QEvent
from PySide6.QtGui import (
    QIcon,
    QMouseEvent,
    QFont,
    QFontDatabase,
    QColor,
    QPalette,
)

from positive_tool import pt

from . import styles
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
        self.close_button = QPushButton("x")

        # 按鈕大小統一設定
        for btn in [
            self.minimize_button,
            self.maximize_button,
            self.close_button,
        ]:
            btn.setFixedSize(40, 30)
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
        self.parent_obj.showMinimized()

    def toggle_maximize(self):
        if self.parent_obj.isMaximized():
            self.parent_obj.showNormal()
            self.maximize_button.setText("□")
        else:
            self.parent_obj.showMaximized()
            self.maximize_button.setText("❐")

    def close_window(self):
        self.parent_obj.close()  # TODO: 在未儲存時詢問


class PasswordBookGui(QMainWindow):
    def __new__(cls, app: QApplication, logger: logging.Logger) -> Self:
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
        self.data: ppb_backend.data_type = {}
        self.data_widgets: list[QWidget] = []  # widgets清單
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
            app_font = QFont(family, 20)  # 調整字體大小
        else:
            app_font = QFont("Microsoft JhengHei", 20)
        self.setFont(app_font)
        # 建立UI
        self._setup_ui()
        self._refresh_data()

    def _setup_ui(self):
        """建立使用者介面"""
        # 主容器
        main_container = QWidget()
        main_layout = QVBoxLayout()
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.setSpacing(0)

        # 自訂標題列
        self.title_bar = CustomTitleBar(self)
        self.title_bar.setFixedHeight(50)
        main_layout.addWidget(self.title_bar)

        # 中央內容區域
        central_widget = QWidget()
        content_layout = QVBoxLayout()
        content_layout.setContentsMargins(20, 40, 20, 20)

        # 頂部工具列
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

        # 資料顯示區域 - 使用QScrollArea
        self.scroll_area = QScrollArea()
        self.scroll_area.setWidgetResizable(True)
        self.scroll_area.setVerticalScrollBarPolicy(
            Qt.ScrollBarPolicy.ScrollBarAlwaysOn
        )
        self.scroll_area.setHorizontalScrollBarPolicy(
            Qt.ScrollBarPolicy.ScrollBarAlwaysOn
        )
        # 設定ScrollArea背景顏色
        scroll_palette = self.scroll_area.palette()
        scroll_palette.setColor(
            QPalette.ColorRole.Window, QColor("#f0f0f0")
        )  # 設定背景色
        self.scroll_area.setPalette(scroll_palette)
        self.scroll_area.setAutoFillBackground(True)
        # 建立內容容器
        self.content_container = QWidget()
        self.content_layout = QVBoxLayout()
        self.content_layout.setAlignment(Qt.AlignmentFlag.AlignTop)
        self.content_layout.setSpacing(15)
        self.content_container.setLayout(self.content_layout)

        # 將內容容器加入scroll area
        self.scroll_area.setWidget(self.content_container)

        content_layout.addWidget(self.scroll_area)
        central_widget.setLayout(content_layout)

        main_layout.addWidget(central_widget)
        main_container.setLayout(main_layout)
        self.setCentralWidget(main_container)

        # 設定視窗屬性
        self.resize(1080, 720)
        self.setWindowTitle(project_infos["project_name"])
        self.title_bar.title_label.setText(project_infos["project_name"])

    def _clear_existing_widgets(self):
        """清除現有元件"""
        for widget in self.data_widgets:
            widget.setParent(None)  # 移除父元件
            widget.deleteLater()  # 延遲刪除
        self.data_widgets.clear()

    def _refresh_data(self):
        """重新整理資料"""
        self.logger.info("開始重新整理資料...")

        # 清除現有元件
        self._clear_existing_widgets()

        # 從後端取得最新資料
        try:
            self.data = self.backend.password_book_get_data()
            self.logger.info(f"從後端取得 {len(self.data)} 筆資料")
        except Exception as e:
            self.logger.error(f"取得後端資料失敗: {e}")
            return

        # 依資料建立UI元件
        for app_name in self.data:
            if app_name == "trash_can":
                continue

            self.logger.info(f"處理應用程式: {app_name}")

            for app_data in self.data[app_name]:
                acc: str = app_data.get("acc", "")
                pwd: str = app_data.get("pwd", "")

                # 建立單一行項目
                row_widget = self._create_app_row(app_name, acc, pwd)
                self.content_layout.addWidget(row_widget)
                self.data_widgets.append(row_widget)

        # 如果沒有資料，顯示提示
        if len([k for k in self.data.keys() if k != "trash_can"]) == 0:
            no_data_label = QLabel("目前沒有任何資料")
            no_data_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
            no_data_label.setStyleSheet(
                "color: gray; font-size: 16px; font-style: italic;"
            )
            self.content_layout.addWidget(no_data_label)

        self.logger.info("資料重新整理完成")

    def _create_app_row(self, app_name: str, acc: str, pwd: str) -> QWidget:
        """建立單一應用程式資料列"""
        row_widget = QWidget()
        row_layout = QHBoxLayout()
        row_layout.setSpacing(10)
        # 應用程式群組
        app_group = self._create_field_group("應用程式：", app_name)
        # 帳號群組
        acc_group = self._create_field_group("帳號：", acc)
        # 密碼群組
        pwd_group = self._create_field_group("密碼：", pwd)
        # 加入佈局
        row_layout.addWidget(app_group)
        row_layout.addSpacing(70)
        row_layout.addWidget(acc_group)
        row_layout.addSpacing(70)
        row_layout.addWidget(pwd_group)
        row_widget.setLayout(row_layout)
        return row_widget

    def _create_field_group(
        self, label_text: str, value_text: str
    ) -> QGroupBox:
        """建立欄位群組"""
        group = QGroupBox()
        layout = QHBoxLayout()
        key_label = QLabel(f"<u>{label_text}</u>")
        value_label = QLabel(value_text)
        value_label.setTextInteractionFlags(
            Qt.TextInteractionFlag.TextSelectableByMouse
            | Qt.TextInteractionFlag.TextSelectableByKeyboard
        )

        layout.addWidget(key_label)
        layout.addWidget(value_label)
        layout.addStretch()

        group.setLayout(layout)
        group.setStyleSheet(styles.group_style)

        return group

    def changeEvent(self, event: QEvent):
        if (
            event.type() == QEvent.Type.WindowStateChange
            and (hasattr(self, "title_bar") is True)
            and self.title_bar is not None
        ):
            if self.isMaximized():
                self.title_bar.maximize_button.setText("❐")
            else:
                self.title_bar.maximize_button.setText("□")
        super().changeEvent(event)


def main(logger):
    app = QApplication([])
    # 設定應用程式樣式
    app.setStyle("Fusion")
    # 字體設定
    font_id = QFontDatabase.addApplicationFont(font_noto_sans_path)
    if font_id != -1:
        family = QFontDatabase.applicationFontFamilies(font_id)[0]
        app_font = QFont(family, 20)
    else:
        app_font = QFont("Microsoft JhengHei", 20)
    app.setFont(app_font)
    window = PasswordBookGui(app, logger)
    window.show()
    icon_path = os.path.join(project_infos["project_path"], "icon.png")
    if os.path.exists(icon_path):
        app.setWindowIcon(QIcon(icon_path))
    app.exec()


if __name__ == "__main__":
    log_dir = os.path.join(project_path, ".logs")
    if not os.path.exists(log_dir):
        os.makedirs(log_dir, exist_ok=True)
    time_now = datetime.datetime.now()
    time_format_str = time_now.strftime("%Y-%d-%m_%H-%M-%S")
    log_file_path = os.path.join(log_dir, f"log_{time_format_str}.log")
    logger = pt.build_logger(log_file_path, f"{project_name}_logger")
    main(logger)
