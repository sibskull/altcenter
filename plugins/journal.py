#!/usr/bin/python3

import plugins
import os
import json
from PyQt5.QtWidgets import QWidget, QVBoxLayout, QHBoxLayout, QStackedWidget, QListWidget, QListWidgetItem, QTextEdit, QSplitter, QLabel, QPushButton, QLineEdit, QComboBox
from PyQt5.QtGui import QStandardItem, QStandardItemModel, QFont
from PyQt5.QtCore import Qt, QProcess, QProcessEnvironment, QLocale

class JournalsWidget(QWidget):
    def __init__(self, main_window = None):
        super().__init__()
        self.main_window = main_window
        self.limit = 100
        self.limit_values = [10, 20, 50, 100, 200, 500, 1000]
        self.page = 0

        self.proc = None
        self.stdout_buf = []
        self.stderr_buf = []
        self.loading = False
        self.has_more_older = False
        self.current_fetch_lines = 0

        self.text = None
        self.btn_prev = None
        self.btn_next = None
        self.combo_limit = None

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

        bottom = QHBoxLayout()

        self.btn_prev = QPushButton(self.tr("Back"))
        self.btn_prev.clicked.connect(self.on_prev_clicked)

        self.btn_next = QPushButton(self.tr("Forward"))
        self.btn_next.clicked.connect(self.on_next_clicked)

        bottom.addStretch(1)
        bottom.addWidget(self.btn_prev)
        bottom.addWidget(self.btn_next)

        bottom.addWidget(QLabel(self.tr("Lines:")))

        self.combo_limit = QComboBox()
        for v in self.limit_values:
            self.combo_limit.addItem(str(v), v)

        idx = self.combo_limit.findData(self.limit)
        if idx >= 0:
            self.combo_limit.setCurrentIndex(idx)

        self.combo_limit.currentIndexChanged.connect(self.on_limit_changed)
        bottom.addWidget(self.combo_limit)

        layout.addLayout(bottom)
        self.setLayout(layout)

        self.update_nav_buttons()

    def initProcess(self):
        self.proc = QProcess(self)
        self.proc.readyReadStandardOutput.connect(self.on_journal_output)
        self.proc.readyReadStandardError.connect(self.on_journal_error)
        self.proc.finished.connect(self.on_journal_finished)

        env = QProcessEnvironment.systemEnvironment()
        self.proc.setProcessEnvironment(env)

    def update_nav_buttons(self):
        self.btn_next.setEnabled((self.page > 0) and (not self.loading))
        self.btn_prev.setEnabled(self.has_more_older and (not self.loading))

    def on_limit_changed(self, idx: int):
        v = self.combo_limit.currentData()
        if v != None:
            self.limit = int(v)
            self.page = 0
            self.loadJournal()

    def on_prev_clicked(self):
        if self.loading:
            return
        self.page += 1
        self.loadJournal()

    def on_next_clicked(self):
        if self.loading:
            return
        if self.page > 0:
            self.page -= 1
            self.loadJournal()

    def loadJournal(self):
        if self.proc != None and self.proc.state() != QProcess.NotRunning:
            self.proc.kill()
            self.proc.waitForFinished(1000)

        self.loading = True
        self.update_nav_buttons()

        self.text.clear()
        self.stdout_buf = []
        self.stderr_buf = []

        fetch_lines = self.limit * (self.page + 1)
        self.current_fetch_lines = fetch_lines

        req_lines = fetch_lines + 1
        self.proc.start("journalctl", ["-b", "--no-pager", "-n", str(req_lines)])

    def on_journal_output(self):
        output = self.proc.readAllStandardOutput().data().decode(errors="replace")
        if output:
            self.stdout_buf.append(output)

    def on_journal_error(self):
        error = self.proc.readAllStandardError().data().decode(errors="replace")
        if error:
            self.stderr_buf.append(error)

    def on_journal_finished(self, exit_code, exit_status):
        out = "".join(self.stdout_buf)
        err = "".join(self.stderr_buf)

        lines = out.splitlines(True)

        if len(lines) > self.current_fetch_lines:
            self.has_more_older = True
            lines = lines[1:]
        else:
            self.has_more_older = False

        total = len(lines)
        if total <= 0:
            self.page = 0
            view = ""
        else:
            max_page = (total - 1) // self.limit
            if self.page > max_page:
                self.page = max_page

            start = total - self.limit * (self.page + 1)
            end = total - self.limit * self.page
            if start < 0:
                start = 0
            if end < 0:
                end = 0
            if end > total:
                end = total

            view = "".join(lines[start:end])

        if err:
            if view and not view.endswith("\n"):
                view += "\n"
            view += err

        self.text.setPlainText(view)

        self.loading = False
        self.update_nav_buttons()


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
