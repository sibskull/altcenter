#!/usr/bin/python3

import plugins
import os
import json
from PyQt5.QtWidgets import QWidget, QVBoxLayout, QHBoxLayout, QStackedWidget, QListWidget, QListWidgetItem, QTextEdit, QSplitter, QLabel, QPushButton, QLineEdit
from PyQt5.QtGui import QStandardItem, QStandardItemModel, QFont, QPalette
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
        self._desired_states = {}
        self._baseline_ready = False
        self._updating_checks = False
        self._apply_in_progress = False

        self.search = QLineEdit()
        self.search.setPlaceholderText(self.tr("Search"))
        self.search.textChanged.connect(self.filterList)

        self.list = QListWidget()
        self.list.currentItemChanged.connect(self.onCurrentItemChanged)
        self.list.itemClicked.connect(self.onItemClicked)
        self.list.itemChanged.connect(self.onItemChanged)

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
        self.btn_apply.setEnabled(False)
        self.btn_toggle_console.clicked.connect(self.toggleConsole)
        self.btn_apply.clicked.connect(self.applySelected)

        self.log = QTextEdit()
        self.log.setReadOnly(True)
        self.log.setMinimumHeight(140)
        self.log.setVisible(False)
        self.log.setPlainText(self.tr("All changes made while applying policies will be shown here.") + "\n")

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
        self.refreshApplyButton()

    def showEvent(self, event):
        super().showEvent(event)
        self.syncStatesFromFiles()
        self.rebuildList()

    def pkgRoot(self):
        return os.path.abspath(os.path.join(os.path.dirname(os.path.abspath(__file__)), ".."))

    def jsonPath(self):
        return os.path.join(self.pkgRoot(), "res", "policies.json")
    
    def currentLanguage(self) -> str:
        return QLocale().name().split('_')[0].lower()

    def loc(self, item: dict, base_key: str) -> str:
        lang = self.currentLanguage()
        if lang == "ru":
            text = item.get(base_key, "")
        else:
            text = item.get(f"{base_key}_{lang}", item.get(base_key, ""))

        if item.get("id") == "deny-system-accounts":
            text = text.replace("UID_MIN", str(self.getSystemUidMin()))

        return text

    def isImmutablePolicy(self, pid):
        return pid in (
            "no-autologin",
            "deny-root-login",
        )

# Условия политик
    def isPolicyVisible(self, pid):
        if pid == "sudo-always-ask-password":
            return os.path.exists("/usr/bin/sudo") or os.path.exists("/bin/sudo")
        return True

    def getSystemUidMin(self):
        for path in ("/tmp/altcenter_login.defs", "/etc/login.defs"):
            try:
                with open(path, "r", encoding="utf-8", errors="replace") as f:
                    for raw in f:
                        line = raw.strip()
                        if not line or line.startswith("#"):
                            continue
                        parts = line.split()
                        if len(parts) >= 2 and parts[0] == "UID_MIN":
                            try:
                                return int(parts[1])
                            except Exception:
                                break
            except Exception:
                pass

        return 1000
# Условия политик

    def immutablePolicyText(self):
        return self.tr("Implemented by default and cannot be changed")

    def immutableItemColor(self):
        return self.palette().color(QPalette.Disabled, QPalette.Text)

    def loc_text(self, item: dict) -> tuple[str, str]:
        title = self.loc(item, "title")

        if self.isImmutablePolicy(item.get("id")):
            description = self.immutablePolicyText()
        else:
            description = self.loc(item, "description")

        return title, description

    def onCurrentItemChanged(self, current, previous):
        if current is None:
            return
        self.onItemClicked(current)

    def expectedFiles(self, pid):
        base = "50-altcenter-" + str(pid)
        return [
            "/etc/lightdm/lightdm.conf.d/" + base + ".conf",
            "/etc/sddm.conf.d/" + base + ".conf",
            "/etc/dconf/db/gdm.d/" + base,
        ]

    def policyEnabledFromFiles(self, pid):
        return any(os.path.exists(p) for p in self.expectedFiles(pid))

    def syncStatesFromFiles(self):
        for item in self._items:
            pid = item.get("id")
            if self.isImmutablePolicy(pid):
                exists = True
            else:
                exists = self.policyEnabledFromFiles(pid)
            self._desired_states[pid] = exists
            self._last_states[pid] = exists
        self._baseline_ready = True
        self.updateVisibleChecksFromStates()
        self.refreshApplyButton()

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

        ids = set()
        for item in self._items:
            pid = item.get("id")
            ids.add(pid)

        self._desired_states = {pid: state for pid, state in self._desired_states.items() if pid in ids}
        self._last_states = {pid: state for pid, state in self._last_states.items() if pid in ids}

        for item in self._items:
            pid = item.get("id")
            if self.isImmutablePolicy(pid):
                exists = True
            else:
                exists = self.policyEnabledFromFiles(pid)
            self._desired_states[pid] = exists
            self._last_states[pid] = exists

        self._baseline_ready = True
        self.rebuildList()

    def rebuildList(self):
        self._updating_checks = True
        self.list.clear()
        query = self.search.text().strip().lower()
        immutable_color = self.immutableItemColor()

        for item in self._items:
            pid = item.get("id")
            if not self.isPolicyVisible(pid):
                continue

            title = self.loc(item, "title")
            if query and query not in title.lower():
                continue

            w = QListWidgetItem(title)
            w.setData(Qt.UserRole, pid)
            w.setFlags(w.flags() | Qt.ItemIsUserCheckable)
            w.setCheckState(Qt.Checked if self._desired_states.get(pid, False) else Qt.Unchecked)

            if self.isImmutablePolicy(pid):
                w.setToolTip(self.immutablePolicyText())
                w.setForeground(immutable_color)

            self.list.addItem(w)

        self._updating_checks = False

        if self.list.count() > 0:
            target_row = -1

            if self._current_id is not None:
                for i in range(self.list.count()):
                    it = self.list.item(i)
                    if it.data(Qt.UserRole) == self._current_id:
                        target_row = i
                        break

            if target_row < 0:
                for i in range(self.list.count()):
                    it = self.list.item(i)
                    if it.data(Qt.UserRole) == "hide-users":
                        target_row = i
                        break

            if target_row >= 0:
                self.list.setCurrentRow(target_row)
            else:
                self.list.setCurrentRow(0)
        self.refreshApplyButton()

    def updateVisibleChecksFromStates(self):
        self._updating_checks = True
        immutable_color = self.immutableItemColor()

        for i in range(self.list.count()):
            it = self.list.item(i)
            pid = it.data(Qt.UserRole)
            it.setCheckState(Qt.Checked if self._desired_states.get(pid, False) else Qt.Unchecked)

            if self.isImmutablePolicy(pid):
                it.setToolTip(self.immutablePolicyText())
                it.setForeground(immutable_color)

        self._updating_checks = False

    def updateChecksFromFiles(self):
        self.syncStatesFromFiles()

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

    def onItemChanged(self, it):
        if self._updating_checks:
            return

        pid = it.data(Qt.UserRole)

        if self.isImmutablePolicy(pid):
            self._updating_checks = True
            it.setCheckState(Qt.Checked)
            self._updating_checks = False
            self._desired_states[pid] = True
            self._last_states[pid] = True
            self.refreshApplyButton()
            return

        self._desired_states[pid] = (it.checkState() == Qt.Checked)
        self.refreshApplyButton()

    def appendLog(self, text):
        self.log.append(text)

    def selectedIds(self):
        ids = []
        for item in self._items:
            pid = item.get("id")
            if not self.isPolicyVisible(pid):
                continue
            if self._desired_states.get(pid, False):
                ids.append(pid)
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

    def hasPendingChanges(self):
        for item in self._items:
            pid = item.get("id")
            if not self.isPolicyVisible(pid):
                continue
            if self.isImmutablePolicy(pid):
                continue
            cur_checked = self._desired_states.get(pid, False)
            prev_checked = self._last_states.get(pid, False)
            if cur_checked != prev_checked:
                return True
        return False

    def refreshApplyButton(self):
        self.btn_apply.setEnabled((not self._apply_in_progress) and self.hasPendingChanges())

    def setApplyInProgress(self, value):
        self._apply_in_progress = value
        self.btn_apply.clearFocus()
        self.list.setEnabled(not value)
        self.search.setEnabled(not value)
        self.refreshApplyButton()

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
                self.syncStatesFromFiles()
            else:
                self.appendLog(self.tr("Policies are not activated; authenticate to apply policies"))
            self.setApplyInProgress(False)
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
        if self._apply_in_progress:
            return
        if not self.hasPendingChanges():
            self.refreshApplyButton()
            return
        if not self.log.isVisible():
            self.btn_toggle_console.click()

        dm = self.active_dm
        root_pieces = []
        titles_root = []

        for item in self._items:
            pid = item.get("id")

            if not self.isPolicyVisible(pid):
                continue

            if self.isImmutablePolicy(pid):
                self._desired_states[pid] = True
                self._last_states[pid] = True
                continue

            cur_checked = self._desired_states.get(pid, False)
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
            self.apply_counter += 1
            summary = str(self.apply_counter) + " " + self.tr("apply")
            self.appendLog(summary)
            script = "set -e; " + " && ".join(root_pieces)
            self.setApplyInProgress(True)
            self.runRoot(["/bin/sh", "-c", script], titles_root)
        else:
            self.syncStatesFromFiles()

class PluginPolicies(plugins.Base):
    requires_admin = True
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
