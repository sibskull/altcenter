#!/usr/bin/python3

import plugins
import os
import json
from PyQt5.QtWidgets import QWidget, QVBoxLayout, QHBoxLayout, QStackedWidget, QListWidget, QListWidgetItem, QTextEdit, QSplitter, QLabel, QPushButton, QLineEdit, QComboBox, QToolButton, QCheckBox, QFileDialog
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
        self.rescan_target = 0

        self.text = None
        self.btn_prev = None
        self.btn_next = None
        self.combo_limit = None

        self.btn_filters = None
        self.filters_popup = None
        self.filter_checks = []
        self.filter_items = []

        self.btn_journal = None
        self.journal_popup = None
        self.journal_checks = []

        self.edit_query = None

        self.combo_export = None
        self.btn_export = None

        self.proc_export = None
        self.proc_formats = None
        self.output_formats = []

        self.current_source = "journalctl"

        self.proc_audit = None

        self.initUI()
        self.initProcess()
        self.loadOutputFormats()
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

        top.addWidget(QLabel(self.tr("Journal:")))

        self.btn_journal = QToolButton()
        self.btn_journal.setText("journalctl")
        self.btn_journal.clicked.connect(self.toggle_journal_popup)
        top.addWidget(self.btn_journal, 0, Qt.AlignLeft)

        top.addSpacing(10)

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
        self.edit_query.returnPressed.connect(self.on_query_apply)
        self.edit_query.textChanged.connect(self.on_query_text_changed)
        top.addWidget(self.edit_query, 1)

        top.addStretch(1)
        layout.addLayout(top)

        self.initJournalPopup()
        self.initFiltersPopup()

        self.text = QTextEdit()
        self.text.setReadOnly(True)
        self.text.setLineWrapMode(QTextEdit.NoWrap)

        f = QFont()
        f.setStyleHint(QFont.Monospace)
        self.text.setFont(f)

        layout.addWidget(self.text, 1)

        bottom = QHBoxLayout()

        self.combo_export = QComboBox()
        self.combo_export.addItem(self.tr("Whole journal"), "all")
        self.combo_export.addItem(self.tr("This page"), "page")
        bottom.addWidget(self.combo_export)

        self.btn_export = QPushButton(self.tr("Save"))
        self.btn_export.clicked.connect(self.on_export_clicked)
        bottom.addWidget(self.btn_export)

        bottom.addStretch(1)

        self.btn_prev = QPushButton(self.tr("Back"))
        self.btn_prev.clicked.connect(self.on_prev_clicked)

        self.btn_next = QPushButton(self.tr("Forward"))
        self.btn_next.clicked.connect(self.on_next_clicked)

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

    def initJournalPopup(self):
        self.journal_popup = QWidget(self, Qt.Popup)
        layout = QVBoxLayout()
        layout.setContentsMargins(8, 8, 8, 8)
        layout.setSpacing(4)

        self.journal_checks = []

        cb_journal = QCheckBox("journalctl")
        cb_journal.setChecked(True)
        cb_journal.stateChanged.connect(self.on_journal_changed)

        cb_audit = QCheckBox("auditd")
        cb_audit.stateChanged.connect(self.on_journal_changed)

        self.journal_checks.append(cb_journal)
        self.journal_checks.append(cb_audit)

        layout.addWidget(cb_journal)
        layout.addWidget(cb_audit)

        self.journal_popup.setLayout(layout)
        self.journal_popup.adjustSize()

    def toggle_journal_popup(self):
        if self.journal_popup.isVisible():
            self.journal_popup.hide()
            return

        self.journal_popup.adjustSize()
        pos = self.btn_journal.mapToGlobal(QPoint(0, self.btn_journal.height()))
        self.journal_popup.move(pos)
        self.journal_popup.show()

    def on_journal_changed(self, state):
        cb = self.sender()
        if state != Qt.Checked:
            return

        for other in self.journal_checks:
            if other != cb:
                other.blockSignals(True)
                other.setChecked(False)
                other.blockSignals(False)

        self.btn_journal.setText(cb.text())
        self.journal_popup.hide()

        if cb.text() == "auditd":
            self.current_source = "auditd"
            self.start_audit_pkexec_test()
            return

        self.current_source = "journalctl"
        self.page = 0
        self.loadJournal()

    def start_audit_pkexec_test(self):
        if self.proc_audit != None and self.proc_audit.state() != QProcess.NotRunning:
            return

        self.text.setPlainText("")

        self.proc_audit.start("pkexec", ["sh", "-c", "true"])

    def on_audit_finished(self, exit_code, exit_status):
        if exit_code == 0:
            self.text.setPlainText("True")
        else:
            self.text.setPlainText("False")

    def format_from_filter(self, selected_filter: str):
        t = (selected_filter or "").strip()

        if not t:
            fmt = "short"
        else:
            i = t.find(" (")
            if i > 0:
                fmt = t[:i].strip()
            else:
                fmt = t.strip()

        tl = (fmt or "").strip().lower()
        if tl.startswith("json"):
            ext = "json"
        elif tl == "export":
            ext = "log"
        else:
            ext = "txt"

        return fmt, ext

    def build_save_filters(self):
        parts = []
        for fmt in self.output_formats:
            _, ext = self.format_from_filter(fmt)
            parts.append(f"{fmt} (*.{ext})")
        return ";;".join(parts)

    def loadOutputFormats(self):
        if self.proc_formats != None and self.proc_formats.state() != QProcess.NotRunning:
            return

        self.proc_formats = QProcess(self)
        self.proc_formats.finished.connect(self.on_formats_finished)

        env = QProcessEnvironment.systemEnvironment()
        self.proc_formats.setProcessEnvironment(env)

        self.proc_formats.start("journalctl", ["-o", "help"])

    def on_formats_finished(self, exit_code, exit_status):
        out = self.proc_formats.readAllStandardOutput().data().decode(errors="replace")
        if exit_code != 0 or not out:
            return

        s = out.replace("\n", " ").replace(",", " ").replace(":", " ")
        tokens = s.split()

        fmts = []
        for t in tokens:
            if t.isalnum() or "-" in t or "_" in t:
                fmts.append(t)

        if fmts:
            self.output_formats = fmts

    def on_export_clicked(self):
        if self.proc_export != None and self.proc_export.state() != QProcess.NotRunning:
            return

        options = QFileDialog.Options()
        options |= QFileDialog.DontUseNativeDialog

        filters = self.build_save_filters()

        path, selected_filter = QFileDialog.getSaveFileName(
            self,
            self.tr("Save log"),
            "journal.txt",
            filters,
            options=options
        )

        if not path:
            return

        mode = self.combo_export.currentData()

        if mode == "page":
            try:
                with open(path, "w", encoding="utf-8", errors="replace") as f:
                    f.write(self.text.toPlainText())
            except:
                pass
            return

        if mode == "all":
            fmt, _ = self.format_from_filter(selected_filter)

            self.btn_export.setEnabled(False)

            self.proc_export = QProcess(self)
            self.proc_export.finished.connect(self.on_export_finished)

            env = QProcessEnvironment.systemEnvironment()
            self.proc_export.setProcessEnvironment(env)

            self.proc_export.setStandardOutputFile(path)

            args = ["--no-pager", "-o", fmt]

            keys = self.get_selected_filter_keys()
            matches = self.build_filter_matches(keys)

            if matches:
                for i, m in enumerate(matches):
                    if i > 0:
                        args.append("+")
                    args.append(m)

            self.proc_export.start("journalctl", args)

    def on_export_finished(self, exit_code, exit_status):
        self.btn_export.setEnabled(True)

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

    def on_query_apply(self):
        self.page = 0
        self.loadJournal()

    def on_query_text_changed(self, text):
        if text.strip() == "":
            self.page = 0
            self.loadJournal()

    def initProcess(self):
        self.proc = QProcess(self)
        self.proc.readyReadStandardOutput.connect(self.on_journal_output)
        self.proc.readyReadStandardError.connect(self.on_journal_error)
        self.proc.finished.connect(self.on_journal_finished)

        env = QProcessEnvironment.systemEnvironment()
        self.proc.setProcessEnvironment(env)

        self.proc_audit = QProcess(self)
        self.proc_audit.finished.connect(self.on_audit_finished)

        env = QProcessEnvironment.systemEnvironment()
        self.proc_audit.setProcessEnvironment(env)

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

    def loadJournal(self, forced_fetch_lines=None):
        if self.proc != None and self.proc.state() != QProcess.NotRunning:
            self.proc.kill()
            self.proc.waitForFinished(1000)

        self.loading = True
        self.update_nav_buttons()

        self.text.clear()
        self.stdout_buf = []
        self.stderr_buf = []

        q = ""
        if self.edit_query != None:
            q = self.edit_query.text().strip()

        base_fetch = self.limit * (self.page + 1)
        fetch_lines = base_fetch

        if q and forced_fetch_lines == None:
            min_fetch = self.limit * 10
            if fetch_lines < min_fetch:
                fetch_lines = min_fetch

        if forced_fetch_lines != None:
            fetch_lines = int(forced_fetch_lines)

        self.rescan_target = base_fetch
        self.current_fetch_lines = fetch_lines

        req_lines = fetch_lines + 1

        args = ["--no-pager", "-n", str(req_lines)]

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

        lines_all = out.splitlines(True)

        if len(lines_all) > self.current_fetch_lines:
            self.has_more_older = True
            lines_all = lines_all[1:]
        else:
            self.has_more_older = False

        q = ""
        if self.edit_query != None:
            q = self.edit_query.text().strip()

        lines = lines_all
        if q:
            ql = q.lower()
            filtered = []
            for ln in lines:
                if ql in ln.lower():
                    filtered.append(ln)
            lines = filtered

            if self.has_more_older and len(lines) < self.rescan_target:
                self.loadJournal(self.current_fetch_lines * 2)
                return

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
