#!/usr/bin/python3

import plugins
import os
import json
from PyQt5.QtWidgets import QWidget, QVBoxLayout, QHBoxLayout, QStackedWidget, QListWidget, QListWidgetItem, QTextEdit, QSplitter, QLabel, QPushButton, QLineEdit
from PyQt5.QtGui import QStandardItem, QStandardItemModel, QFont
from PyQt5.QtCore import Qt, QProcess, QProcessEnvironment, QLocale

class PoliciesWindow(QWidget):
    def __init__(self, main_window=None):
        super().__init__()
        self.main_window = main_window
        self._items = []
        self._current_id = None
        self.active_dm = "any"
        self.procs = []
        self.apply_counter = 0
        self._last_states = {}
        self._baseline_ready = False

        self.search = QLineEdit()
        self.search.setPlaceholderText(self.tr("Search"))
        self.search.textChanged.connect(self.filterList)

        self.list = QListWidget()
        self.list.itemClicked.connect(self.onItemClicked)

        self.info_title = QLabel()
        self.info_title.setWordWrap(True)
        self.info_title.setAlignment(Qt.AlignLeft | Qt.AlignTop)
        self.info_title.setFont(QFont(self.font().family(), 11, QFont.Bold))

        self.info_text = QTextEdit()
        self.info_text.setReadOnly(True)
        self.info_text.setMinimumHeight(120)
        self.info_text.setMaximumHeight(220)

        self.btn_toggle_console = QPushButton(self.tr("Show console"))
        self.btn_apply = QPushButton(self.tr("Apply"))
        self.btn_toggle_console.clicked.connect(self.toggleConsole)
        self.btn_apply.clicked.connect(self.applySelected)

        self.log = QTextEdit()
        self.log.setReadOnly(True)
        self.log.setMinimumHeight(140)
        self.log.setVisible(False)

        left = QVBoxLayout()
        left.addWidget(self.search)
        left.addWidget(self.list)

        right = QVBoxLayout()
        right.addWidget(self.info_title)
        right.addWidget(self.info_text)

        left_w = QWidget()
        left_w.setLayout(left)
        right_w = QWidget()
        right_w.setLayout(right)
        right_w.setVisible(False)
        self.right_panel = right_w

        top = QSplitter(Qt.Horizontal)
        top.addWidget(left_w)
        top.addWidget(right_w)
        top.setStretchFactor(0, 3)
        top.setStretchFactor(1, 1)

        buttons = QHBoxLayout()
        buttons.addWidget(self.btn_toggle_console)
        buttons.addStretch(1)
        buttons.addWidget(self.btn_apply)

        root = QVBoxLayout()
        root.addWidget(top)
        root.addLayout(buttons)
        root.addWidget(self.log)
        self.setLayout(root)

        self.loadFromJson()
        self.active_dm = self.detectDisplayManager()

    def pkgRoot(self):
        return os.path.abspath(os.path.join(os.path.dirname(os.path.abspath(__file__)), ".."))

    def jsonPath(self):
        return os.path.join(self.pkgRoot(), "res", "policies.json")
    
    def currentLanguage(self) -> str:
        return QLocale().name().split('_')[0].lower()

    def loc(self, item: dict, base_key: str) -> str:
        lang = self.currentLanguage()
        if lang == "ru":
            return item.get(base_key, "")
        return item.get(f"{base_key}_{lang}", item.get(base_key, ""))

    def loc_text(self, item: dict) -> tuple[str, str]:
        print(self.loc(item, "title"), self.loc(item, "description"))
        return self.loc(item, "title"), self.loc(item, "description")

    def expectedFiles(self, pid):
        base = "50-altcenter-" + str(pid)
        return [
            "/etc/lightdm/lightdm.conf.d/" + base + ".conf",
            "/etc/sddm.conf.d/" + base + ".conf",
            "/etc/dconf/db/gdm.d/" + base,
        ]

    def loadFromJson(self):
        self._items = []
        path = self.jsonPath()
        try:
            with open(path, "r", encoding="utf-8") as f:
                data = json.load(f)
            for item in data.get("policies", []):
                self._items.append(item)
        except Exception:
            self._items = []
        self.rebuildList()

    def rebuildList(self):
        self.list.clear()
        query = self.search.text().strip().lower()
        for item in self._items:
            title = self.loc(item, "title")
            if query and query not in title.lower():
                continue
            w = QListWidgetItem(title)
            w.setData(Qt.UserRole, item.get("id"))
            w.setFlags(w.flags() | Qt.ItemIsUserCheckable)
            w.setCheckState(Qt.Unchecked)
            self.list.addItem(w)
        if self.list.count() > 0:
            self.list.setCurrentRow(0)
        self.updateChecksFromFiles()
        if not self._baseline_ready:
            st = {}
            for i in range(self.list.count()):
                it = self.list.item(i)
                st[it.data(Qt.UserRole)] = (it.checkState() == Qt.Checked)
            self._last_states = st
            self._baseline_ready = True

    def updateChecksFromFiles(self):
        for i in range(self.list.count()):
            it = self.list.item(i)
            pid = it.data(Qt.UserRole)
            exists = any(os.path.exists(p) for p in self.expectedFiles(pid))
            it.setCheckState(Qt.Checked if exists else Qt.Unchecked)

    def filterList(self, _):
        self.rebuildList()

    def getItem(self, pid):
        for item in self._items:
            if item.get("id") == pid:
                return item
        return None

    def onItemClicked(self, it):
        pid = it.data(Qt.UserRole)
        self._current_id = pid
        data = self.getItem(pid)
        if not data:
            return
        t, d = self.loc_text(data)
        self.info_title.setText(t)
        self.info_text.setPlainText(d)
        if not self.right_panel.isVisible():
            self.right_panel.setVisible(True)

    def appendLog(self, text):
        self.log.append(text)

    def selectedIds(self):
        ids = []
        for i in range(self.list.count()):
            it = self.list.item(i)
            if it.checkState() == Qt.Checked:
                ids.append(it.data(Qt.UserRole))
        return ids

    def toggleConsole(self):
        vis = self.log.isVisible()
        self.log.setVisible(not vis)
        if self.log.isVisible():
            self.btn_toggle_console.setText(self.tr("Hide console"))
        else:
            self.btn_toggle_console.setText(self.tr("Show console"))

    def detectDisplayManager(self):
        try:
            path = os.path.realpath("/etc/systemd/system/display-manager.service")
            base = os.path.basename(path).lower()
            if "lightdm" in base:
                return "lightdm"
            if "gdm" in base:
                return "gdm"
            if "sddm" in base:
                return "sddm"
        except Exception:
            pass
        return "any"

    def sessionProcessEnvironment(self):
        env = QProcessEnvironment.systemEnvironment()
        keys = ("DISPLAY", "XAUTHORITY", "DBUS_SESSION_BUS_ADDRESS", "XDG_RUNTIME_DIR", "WAYLAND_DISPLAY")
        for k in keys:
            v = os.environ.get(k)
            if v and not env.contains(k):
                env.insert(k, v)
        return env

    def runRoot(self, args, messages=None):
        p = QProcess(self)
        p.setProcessEnvironment(self.sessionProcessEnvironment())
        p.setProgram("pkexec")
        p.setArguments(args)
        p.setProcessChannelMode(QProcess.MergedChannels)
        def _finished(code, status, msgs=messages, proc=p):
            if code == 0:
                if msgs:
                    for t, s in msgs:
                        self.appendLog(t + " - " + s)
                self.updateChecksFromFiles()
                st = {}
                for i in range(self.list.count()):
                    it = self.list.item(i)
                    st[it.data(Qt.UserRole)] = (it.checkState() == Qt.Checked)
                self._last_states = st
            else:
                self.appendLog(self.tr("Policies are not activated; authenticate to apply policies"))
            self.appendLog("")
            if proc in self.procs:
                self.procs.remove(proc)
        p.finished.connect(_finished)
        self.procs.append(p)
        p.start()

    def runUser(self, args):
        program = args[0]
        arguments = args[1:] if len(args) > 1 else []
        QProcess.startDetached(program, arguments)

    def applySelected(self):
        if self.list.count() == 0:
            return
        if not self.log.isVisible():
            self.btn_toggle_console.click()
        dm = self.active_dm
        self.apply_counter += 1
        root_pieces = []
        titles_root = []
        for i in range(self.list.count()):
            it = self.list.item(i)
            pid = it.data(Qt.UserRole)
            item = self.getItem(pid)
            if not item:
                continue
            cur_checked = (it.checkState() == Qt.Checked)
            prev_checked = self._last_states.get(pid, False)
            should_process = (cur_checked != prev_checked)
            if not should_process:
                continue
            title = self.loc(item, "title") or self.tr("Policy")
            mode = "apply" if cur_checked else "revert"
            status = self.tr("activated") if mode == "apply" else self.tr("deactivated")
            added = False
            for step in item.get(mode, []):
                if step.get("type") != "cmd":
                    continue
                step_dm = step.get("dm", "any")
                if step_dm != "any" and step_dm != dm:
                    continue
                args = step.get("run", [])
                if not args:
                    continue
                if len(args) >= 3 and args[0] == "/bin/sh" and args[1] == "-c":
                    root_pieces.append(args[2])
                else:
                    root_pieces.append(" ".join(args))
                added = True
            if added:
                titles_root.append((title, status))
        if root_pieces:
            summary = str(self.apply_counter) + " " + self.tr("apply")
            self.appendLog(summary)
            script = "set -e; " + " && ".join(root_pieces)
            self.runRoot(["/bin/sh", "-c", script], titles_root)
        else:
            summary = str(self.apply_counter) + " " + self.tr("apply") + ": " + self.tr("no changes")
            self.appendLog(summary)
            self.appendLog("")

class PluginPolicies(plugins.Base):
    def __init__(self, plist: QStandardItemModel = None, pane: QStackedWidget = None):
        super().__init__("policies", 80, plist, pane)
        if self.plist != None and self.pane != None:
            self.node = QStandardItem(self.tr("Policy"))
            self.node.setData(self.name)
            self.plist.appendRow([self.node])
            self.pane.addWidget(QWidget())

    def _do_start(self, idx: int):
        main_window = self.pane.window()
        main_widget = PoliciesWindow(main_window)
        self.pane.insertWidget(idx, main_widget)
