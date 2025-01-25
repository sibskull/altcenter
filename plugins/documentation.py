#!/usr/bin/python3

from PyQt5.QtWidgets import QTextBrowser
from PyQt5.QtGui import QStandardItem, QFont, QTextDocument
from PyQt5.QtCore import QUrl

import locale, os

import plugins

class PluginDocumentation(plugins.Base):
    def __init__(self):
        super().__init__("documentation", 20)
        self.node = None

    def start(self, plist, pane):
        self.node = QStandardItem(self.tr("Documentation"))
        self.node.setData(self.getName())
        plist.appendRow([self.node])

        self.text_browser = QTextBrowser()
        self.text_browser.setOpenExternalLinks(True)
        self.index = pane.addWidget(self.text_browser)

        current_file = os.path.abspath(__file__)
        current_dir = os.path.dirname(current_file)
        parent_dir = os.path.dirname(current_dir)
        file_name = 'docs_' + locale.getlocale()[0].split( '_' )[0] + '.md'
        file_path = os.path.join(parent_dir, 'translations', file_name)

        if os.path.isfile(file_path):
            url = QUrl(file_path)
            self.text_browser.setSource(url, QTextDocument.ResourceType.MarkdownResource)
        else:
            file_path = os.path.join(parent_dir, 'translations', 'docs_en.md')
            if os.path.isfile(file_path):
                url = QUrl(file_path)
                self.text_browser.setSource(url, QTextDocument.ResourceType.MarkdownResource)
            else:
                self.text_browser.setHtml(f"File '{file_path}' not found.")
