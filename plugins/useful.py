#!/usr/bin/python3

from PyQt5.QtWidgets import QVBoxLayout, QFrame, QStackedWidget, QWidget
from PyQt5.QtGui import QStandardItem, QStandardItemModel, QPalette, QDesktopServices
from PyQt5.QtCore import QUrl
from PyQt5.QtWebEngineWidgets import QWebEngineView, QWebEnginePage

import locale, os, markdown

import plugins
import my_utils_pyqt5


class UsefulWebPage(QWebEnginePage):
    def acceptNavigationRequest(self, url, navigation_type, is_main_frame):
        if navigation_type == QWebEnginePage.NavigationTypeLinkClicked:
            QDesktopServices.openUrl(url)
            return False
        return super().acceptNavigationRequest(url, navigation_type, is_main_frame)


class PluginUseful(plugins.Base):
    def __init__(self, plist: QStandardItemModel=None, pane: QStackedWidget = None):
        super().__init__("useful", 50, plist, pane)
        # self.node = None

        if self.plist != None and self.pane != None:
            self.node = QStandardItem(self.tr("Useful Information"))
            self.node.setData(self.name)
            self.plist.appendRow([self.node])
            self.pane.addWidget(QWidget())


    def _do_start(self, idx: int):
        frame = QFrame()
        frame.setFrameStyle(QFrame.Shape.StyledPanel | QFrame.Shadow.Sunken)

        self.text_browser = QWebEngineView()
        self.text_browser.setPage(UsefulWebPage(self.text_browser))

        # Добавляем QWebEngineView в QFrame
        frame_layout = QVBoxLayout(frame)
        frame_layout.setContentsMargins(0, 0, 0, 0)
        frame_layout.addWidget(self.text_browser)

        # Добавляем QFrame в основной layout
        self.pane.insertWidget(idx, frame)

        px = my_utils_pyqt5.point_size_to_pixels(self.pane.font().pointSize())
        if px > 0:
            px = px + 1
        else:
            px = 14

        palette = self.pane.window().palette()
        base_color = palette.color(QPalette.Base).name()
        text_color = palette.color(QPalette.Text).name()
        alt_base_color = palette.color(QPalette.AlternateBase).name()
        link_color = palette.color(QPalette.Link).name()

        current_file = os.path.abspath(__file__)
        current_dir = os.path.dirname(current_file)
        parent_dir = os.path.dirname(current_dir)
        file_name = 'useful_' + locale.getlocale()[0].split( '_' )[0] + '.md'
        file_path = os.path.join(parent_dir, 'translations', file_name)

        def read_file(file_name: str) -> str:
            """Чтение Markdown текста из файла"""
            try:
                with open(file_name, 'r', encoding='utf-8') as file:
                    markdown_text = file.read()
            except FileNotFoundError:
                markdown_text = "Ошибка: файл не найден!"
            return markdown_text


        if os.path.isfile(file_path):
            markdown_text = read_file(file_path)
        else:
            file_path = os.path.join(parent_dir, 'translations', 'useful_en.md')
            if os.path.isfile(file_path):
                markdown_text = read_file(file_path)
            else:
                markdown_text = f"File '{file_path}' not found."


        html_text = markdown.markdown(markdown_text)

        # self.text_browser.setStyleSheet("""
        #     QTextBrowser {
        #         font-family: Arial, sans-serif;
        #         font-size: 14px;
        #     }
        # """)

        styled_html = f"""
        <!DOCTYPE html>
        <html>
        <head>
        <meta charset="utf-8">
        <style>
        html, body {{
            /*font-family: Monospace, Liberation Mono;*/
            background-color: {base_color};
            color: {text_color};
            font-size: {px}px;
        }}
        body {{
            margin: 12px;
        }}
        a {{
            color: {link_color};
        }}
        code {{
            /*font-family: Monospace, Liberation Mono, DejaVu Sans Mono;*/
            color: {text_color};
            background-color: {alt_base_color};
            padding: 1px 0px;
            font-weight: 540;
            border-radius: 2px;
        }}
        pre {{
            /*font-family: Monospace, Liberation Mono, DejaVu Sans Mono;*/
            color: {text_color};
            background-color: {alt_base_color};
            margin: 15px;
            padding: 10px 20px;
            border-radius: 4px;
            font-weight: 540;
            box-sizing: border-box;
            white-space: pre-wrap;
        }}
        pre code {{
            background-color: transparent;
            padding: 0;
        }}
        </style>
        </head>
        <body>
        {html_text}
        </body>
        </html>
        """

        self.text_browser.page().setBackgroundColor(palette.color(QPalette.Base))
        self.text_browser.setHtml(styled_html)
