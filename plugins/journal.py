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
        self.limit = 100
        self.proc = None

        self.initUI()
        self.initProcess()
        self.loadJournal()

    def initUI(self):
        layout = QVBoxLayout()
        layout.setContentsMargins(10, 10, 10, 10)

        self.text = QTextEdit()
        self.text.setReadOnly(True)
        self.text.setLineWrapMode(QTextEdit.NoWrap)

        f = QFont()
        f.setStyleHint(QFont.Monospace)
        self.text.setFont(f)

        layout.addWidget(self.text, 1)
        self.setLayout(layout)

    def initProcess(self):
        self.proc = QProcess(self)
        self.proc.readyReadStandardOutput.connect(self.on_journal_output)
        self.proc.readyReadStandardError.connect(self.on_journal_error)
        self.proc.finished.connect(self.on_journal_finished)

        env = QProcessEnvironment.systemEnvironment()
        self.proc.setProcessEnvironment(env)

    def loadJournal(self):
        if self.proc != None and self.proc.state() != QProcess.NotRunning:
            self.proc.kill()
            self.proc.waitForFinished(1000)

        self.text.clear()
        self.proc.start("journalctl", ["-b", "--no-pager", "-n", str(self.limit)])

    def append_to_console(self, text, is_error=False):
        if not text:
            return
        self.text.moveCursor(self.text.textCursor().End)
        self.text.insertPlainText(text)
        self.text.moveCursor(self.text.textCursor().End)

    def on_journal_output(self):
        output = self.proc.readAllStandardOutput().data().decode(errors="replace")
        self.append_to_console(output)

    def on_journal_error(self):
        error = self.proc.readAllStandardError().data().decode(errors="replace")
        self.append_to_console(error, is_error=True)

    def on_journal_finished(self, exit_code, exit_status):
        pass


class PluginJournals(plugins.Base):
    def __init__(self, plist: QStandardItemModel=None, pane: QStackedWidget = None):
        super().__init__("journals", 100, plist, pane)

        if self.plist != None and self.pane != None:
            self.node = QStandardItem(self.tr("System logs"))
            self.node.setData(self.name)
            self.plist.appendRow([self.node])
            self.pane.addWidget(QWidget())

    def _do_start(self, idx: int):
        main_window = self.pane.window()
        main_widget = JournalsWidget(main_window)
        self.pane.insertWidget(idx, main_widget)
