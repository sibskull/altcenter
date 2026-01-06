#!/usr/bin/python3

import plugins
import os
import json
from PyQt5.QtWidgets import QWidget, QVBoxLayout, QHBoxLayout, QStackedWidget, QListWidget, QListWidgetItem, QTextEdit, QSplitter, QLabel, QPushButton, QLineEdit
from PyQt5.QtGui import QStandardItem, QStandardItemModel, QFont
from PyQt5.QtCore import Qt, QProcess, QProcessEnvironment, QLocale

class JournalsWidget(QWidget):
    def __init__(self, main_window = None):
        super().__init__()
        self.main_window = main_window

        self.proc = None
        self.usage_value = None

        self.initUI()
        self.loadUsage()

    def initUI(self):
        layout = QVBoxLayout()
        layout.setContentsMargins(10, 10, 10, 10)

        top = QHBoxLayout()

        top.addWidget(QLabel(self.tr("Current log usage:")))

        self.usage_value = QLineEdit()
        self.usage_value.setReadOnly(True)
        self.usage_value.setText("")
        top.addWidget(self.usage_value, 1)

        top.addStretch(1)
        layout.addLayout(top)

        layout.addStretch(1)
        self.setLayout(layout)

    def loadUsage(self):
        self.proc = QProcess(self)
        env = QProcessEnvironment.systemEnvironment()
        self.proc.setProcessEnvironment(env)
        self.proc.finished.connect(self.on_finished)
        self.proc.start("journalctl", ["--disk-usage"])

    def on_finished(self, exit_code, exit_status):
        out = self.proc.readAllStandardOutput().data().decode(errors="replace").strip()
        err = self.proc.readAllStandardError().data().decode(errors="replace").strip()

        if exit_code == 0 and out:
            size = out
            marker = "take up "
            i = out.find(marker)
            if i >= 0:
                j = out.find(" in", i + len(marker))
                if j > i:
                    size = out[i + len(marker):j].strip()
            self.usage_value.setText(size)
            return

        if err:
            self.usage_value.setText(err)
        else:
            self.usage_value.setText(self.tr("Failed to read log usage."))


class PluginJournals(plugins.Base):
    def __init__(self, plist: QStandardItemModel=None, pane: QStackedWidget = None):
        super().__init__("journals_settings", 110, plist, pane)

        if self.plist != None and self.pane != None:
            self.node = QStandardItem(self.tr("System logs settings"))
            self.node.setData(self.name)
            self.plist.appendRow([self.node])
            self.pane.addWidget(QWidget())

    def _do_start(self, idx: int):
        main_window = self.pane.window()
        main_widget = JournalsWidget(main_window)
        self.pane.insertWidget(idx, main_widget)
