#!/usr/bin/python3

from PyQt5.QtWidgets import QWidget, QVBoxLayout, QFrame
from PyQt5.QtGui import QStandardItem
from PyQt5.QtWebEngineWidgets import QWebEngineView

import locale, os, markdown

import plugins


class PluginUseful(plugins.Base):
    def __init__(self):
        super().__init__(50)
        self.node = None
        self.useful_widget = None

    # def start(self, plist, pane):
    #     self.node = QStandardItem(self.tr("Useful Information"))
    #     plist.appendRow([self.node])

    #     self.useful_widget = UsefulWidget()
    #     pane.addWidget(self.useful_widget)

    def start(self, plist, pane):
        self.node = QStandardItem(self.tr("Useful Information"))
        plist.appendRow([self.node])

        # widget = QWidget()
        # self.setCentralWidget(widget)
        # layout = QVBoxLayout(widget)
        # layout.setContentsMargins(0, 0, 0, 0)
        frame = QFrame()
        frame.setFrameStyle(QFrame.Shape.StyledPanel | QFrame.Shadow.Sunken)

        self.text_browser = QWebEngineView()

        # Добавляем QWebEngineView в QFrame
        frame_layout = QVBoxLayout(frame)
        frame_layout.setContentsMargins(0, 0, 0, 0)
        frame_layout.addWidget(self.text_browser)

        # Добавляем QFrame в основной layout
        # layout.addWidget(frame)
        pane.addWidget(frame)



        # self.index = pane.addWidget(self.text_browser)
        # self.index = pane.addWidget(widget)

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
        <style>
        code {{
            font-family: Liberation Mono, DejaVu Sans Mono;
            color: #101010;
            background-color: #dcdcdc;
            padding: 1px 0px;
            font-weight: 540;
            border-radius: 2px;
        }}
        pre {{
            font-family: Liberation Mono, DejaVu Sans Mono;
            background-color: #dcdcdc;
            margin: 15px;
            padding: 10px 20px;
            border-radius: 4px;
            font-weight: 540;
            box-sizing: border-box;
        }}
        </style>
        {html_text}
        """

        self.text_browser.setHtml(styled_html)
