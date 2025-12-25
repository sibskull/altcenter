#!/usr/bin/python3

import plugins
import os
import json
from PyQt5.QtWidgets import QWidget, QVBoxLayout, QHBoxLayout, QStackedWidget, QListWidget, QListWidgetItem, QTextEdit, QSplitter, QLabel, QPushButton, QLineEdit, QComboBox, QToolButton, QCheckBox
from PyQt5.QtGui import QStandardItem, QStandardItemModel, QFont
from PyQt5.QtCore import Qt, QProcess, QProcessEnvironment, QLocale, QPoint

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

        self.btn_filters = None
        self.filters_popup = None
        self.filter_checks = []
        self.filter_items = []

        self.edit_query = None

        self.initUI()
        self.initProcess()
        self.loadJournal()

    def initUI(self):
        self.filter_items = [
            ("kernel", self.tr("Kernel")),
            ("sshd.service", "sshd.service"),
            ("NetworkManager.service", "NetworkManager.service"),
            ("systemd-logind.service", "systemd-logind.service"),
            ("polkit.service", "polkit.service"),
            ("lightdm.service", "lightdm.service"),
            ("wpa_supplicant.service", "wpa_supplicant.service"),
            ("udisks2.service", "udisks2.service"),
            ("packagekit.service", "packagekit.service"),
            ("xrdp.service", "xrdp.service"),
            ("dbus.service", "dbus.service"),
        ]

        layout = QVBoxLayout()
        layout.setContentsMargins(10, 10, 10, 10)

        top = QHBoxLayout()

        top.addWidget(QLabel(self.tr("Filters:")))

        self.btn_filters = QToolButton()
        self.btn_filters.setText(self.tr("Select filters"))
        self.btn_filters.clicked.connect(self.toggle_filters_popup)
        top.addWidget(self.btn_filters, 0, Qt.AlignLeft)

        top.addSpacing(10)
        top.addWidget(QLabel(self.tr("Text:")))

        self.edit_query = QLineEdit()
        self.edit_query.setPlaceholderText(self.tr("Type to filter..."))
        self.edit_query.setClearButtonEnabled(True)
        top.addWidget(self.edit_query, 1)

        top.addStretch(1)
        layout.addLayout(top)

        self.initFiltersPopup()

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

        bottom.addSpacing(10)
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

    def initFiltersPopup(self):
        self.filters_popup = QWidget(self, Qt.Popup)
        popup_layout = QVBoxLayout()
        popup_layout.setContentsMargins(8, 8, 8, 8)
        popup_layout.setSpacing(4)

        self.filter_checks = []
        for key, title in self.filter_items:
            cb = QCheckBox(title)
            cb.setProperty("filter_key", key)
            cb.stateChanged.connect(self.on_filters_changed)
            popup_layout.addWidget(cb)
            self.filter_checks.append(cb)

        self.filters_popup.setLayout(popup_layout)
        self.filters_popup.adjustSize()

    def toggle_filters_popup(self):
        if self.filters_popup.isVisible():
            self.filters_popup.hide()
            return

        self.filters_popup.adjustSize()
        pos = self.btn_filters.mapToGlobal(QPoint(0, self.btn_filters.height()))
        self.filters_popup.move(pos)
        self.filters_popup.show()

    def get_selected_filter_keys(self):
        selected = []
        for cb in self.filter_checks:
            if cb.isChecked():
                k = cb.property("filter_key")
                if k != None:
                    selected.append(str(k))
        return selected

    def build_filter_matches(self, keys):
        match_list = []

        if "kernel" in keys:
            match_list.append("_TRANSPORT=kernel")

        for k in keys:
            if k.endswith(".service"):
                match_list.append(f"_SYSTEMD_UNIT={k}")

        uniq = []
        s = set()
        for m in match_list:
            if m not in s:
                s.add(m)
                uniq.append(m)

        return uniq

    def apply_filters_text(self):
        selected_titles = []
        for cb in self.filter_checks:
            if cb.isChecked():
                selected_titles.append(cb.text())

        if selected_titles:
            self.btn_filters.setText(", ".join(selected_titles))
        else:
            self.btn_filters.setText(self.tr("Select filters"))

    def on_filters_changed(self, state):
        self.apply_filters_text()
        self.page = 0
        self.loadJournal()

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

        args = ["-b", "--no-pager", "-n", str(req_lines)]

        keys = self.get_selected_filter_keys()
        matches = self.build_filter_matches(keys)

        if matches:
            for i, m in enumerate(matches):
                if i > 0:
                    args.append("+")
                args.append(m)

        self.proc.start("journalctl", args)

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
