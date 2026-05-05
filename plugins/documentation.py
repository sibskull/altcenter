#!/usr/bin/python3

from PyQt6.QtWidgets import QTextBrowser, QPushButton, QVBoxLayout, QWidget, QStackedWidget
from PyQt6.QtGui import QStandardItem, QStandardItemModel, QDesktopServices
from PyQt6.QtCore import QUrl

import locale, os

import plugins

import my_utils

class PluginDocumentation(plugins.Base):
    def __init__(self, plist: QStandardItemModel=None, pane: QStackedWidget = None):
        super().__init__("documentation", 20, plist, pane)

        if self.plist != None and self.pane != None:
            self.node = QStandardItem(self.tr("Documentation"))
            self.node.setData(self.name)
            self.plist.appendRow([self.node])
            self.pane.addWidget(QWidget())


    def _do_start(self, idx: int):
        self.text_browser = QTextBrowser()
        self.text_browser.setOpenExternalLinks(True)

        os_info = my_utils.parse_os_release()
        distro_name = self.get_doc_package_name(os_info.get("MY_NAME"))
        doc_path = ""
        if distro_name:
            doc_path = f"/usr/share/doc/{distro_name}/index.html"

        layout = QVBoxLayout()
        layout.addWidget(self.text_browser)

        if doc_path and os.path.exists(doc_path):
            button = QPushButton(self.tr("Open ALT Linux documentation"))
            button.clicked.connect(lambda: QDesktopServices.openUrl(QUrl.fromLocalFile(doc_path)))
            layout.addWidget(button)

        container = QWidget()
        container.setLayout(layout)
        self.pane.insertWidget(idx, container)

        current_file = os.path.abspath(__file__)
        current_dir = os.path.dirname(current_file)
        parent_dir = os.path.dirname(current_dir)
        file_name = 'docs_' + locale.getlocale()[0].split('_')[0] + '.md'
        file_path = os.path.join(parent_dir, 'translations', file_name)

        def read_file(path: str) -> str:
            with open(path, 'r', encoding='utf-8') as file:
                return file.read()

        if os.path.isfile(file_path):
            self.text_browser.setMarkdown(read_file(file_path))
        else:
            file_path = os.path.join(parent_dir, 'translations', 'docs_en.md')
            if os.path.isfile(file_path):
                self.text_browser.setMarkdown(read_file(file_path))
            else:
                self.text_browser.setHtml(f"File '{file_path}' not found.")


    def get_doc_package_name(self, name: str) -> str:
        mapping = {
            'ALT Education': 'alt-education',
            'ALT Workstation': 'alt-workstation',
            'ALT Workstation K': 'alt-kworkstation',
        }

        return mapping.get(name, "")