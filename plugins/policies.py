#!/usr/bin/python3

import plugins
import os
import json
import subprocess
import shlex
from PyQt6.QtWidgets import QWidget, QVBoxLayout, QHBoxLayout, QStackedWidget, QListWidget, QListWidgetItem, QTextEdit, QSplitter, QLabel, QPushButton, QLineEdit
from PyQt6.QtGui import QStandardItem, QStandardItemModel, QFont, QPalette
from PyQt6.QtCore import Qt, QProcess, QProcessEnvironment, QLocale

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
        self._package_states = {}

        self.search = QLineEdit()
        self.search.setPlaceholderText(self.tr("Search"))
        self.search.textChanged.connect(self.filterList)

        self.list = QListWidget()
        self.list.currentItemChanged.connect(self.onCurrentItemChanged)
        self.list.itemClicked.connect(self.onItemClicked)
        self.list.itemChanged.connect(self.onItemChanged)

        self.info_title = QLabel()
        self.info_title.setTextInteractionFlags(
            Qt.TextInteractionFlag.TextSelectableByMouse | Qt.TextInteractionFlag.TextSelectableByKeyboard
        )
        self.info_title.setFocusPolicy(Qt.FocusPolicy.StrongFocus)
        self.info_title.setWordWrap(True)
        self.info_title.setAlignment(Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignTop)
        self.info_title.setFont(QFont(self.font().family(), 11, QFont.Weight.Bold))

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

        top = QSplitter(Qt.Orientation.Horizontal)
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

        if pid == "deny-root-ssh-login":
            return (
                os.path.exists("/etc/openssh/sshd_config")
                or os.path.exists("/usr/sbin/sshd")
                or os.path.exists("/sbin/sshd")
            )

        return True

    def policyRequiredPackage(self, pid):
        pid = str(pid or "").lower()

        if "podman" in pid:
            return "podman"

        return None

    def isPolicyAvailable(self, pid):
        if pid == "no-username-autocomplete" and self.active_dm == "gdm":
            return False
        package = self.policyRequiredPackage(pid)
        if not package:
            return True

        if package in self._package_states:
            return self._package_states[package]

        try:
            result = subprocess.run(
                ["rpm", "-q", package],
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL,
                check=False,
            )
            self._package_states[package] = (result.returncode == 0)
        except Exception:
            self._package_states[package] = False

        return self._package_states[package]

    def unavailablePolicyText(self, pid):
        if pid == "no-username-autocomplete" and self.active_dm == "gdm":
            return self.tr("This policy is not supported by GDM.")
        package = self.policyRequiredPackage(pid)
        if not package:
            return ""

        command = "'sudo apt-get install " + package + "'"

        if self.currentLanguage() == "ru":
            return "Установите пакет " + package + " и перезапустите ALT Center.\n\nКоманда:\n" + command

        return "Install the " + package + " package and restart ALT Center.\n\nCommand:\n" + command

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
        return self.palette().color(QPalette.ColorGroup.Disabled, QPalette.ColorRole.Text)

    def loc_text(self, item: dict) -> tuple[str, str]:
        title = self.loc(item, "title")

        if self.isImmutablePolicy(item.get("id")):
            description = self.loc(item, "description") + "\n\n" + self.immutablePolicyText()
        elif not self.isPolicyAvailable(item.get("id")):
            description = self.unavailablePolicyText(item.get("id"))
        else:
            description = self.loc(item, "description")

        return title, description

    def onCurrentItemChanged(self, current, previous):
        if current is None:
            return
        self.onItemClicked(current)

    def expectedFiles(self, pid):
        return ["/var/lib/altcenter/policies/states.json"]

    def readPolicyStates(self, strict=False):
        try:
            with open(self.expectedFiles("")[0], "r", encoding="utf-8") as f:
                states = json.load(f)
            if not isinstance(states, dict):
                raise ValueError("Invalid policy state file")
            return states
        except FileNotFoundError:
            return {}
        except (OSError, ValueError):
            if strict:
                raise
            return {}

    def policyEnabledFromFiles(self, pid):
        states = self.readPolicyStates()
        saved_dm = states.get("__display_manager")
        if saved_dm and self.active_dm != "any" and saved_dm != self.active_dm:
            if self.policyUsesDisplayManager(pid):
                return False
        return bool(states.get(pid, False))

    def policyUsesDisplayManager(self, pid):
        item = self.getItem(pid)
        if not item:
            return False
        configurations = []
        for dm in ("gdm", "lightdm", "sddm"):
            commands = []
            for mode in ("apply", "revert"):
                commands.append(tuple(tuple(step.get("run", [])) for step in item.get(mode, []) if step.get("dm", "any") in ("any", dm)))
            configurations.append(tuple(commands))
        return len(set(configurations)) > 1

    def syncStatesFromFiles(self, preserve_pending=False):
        for item in self._items:
            pid = item.get("id")
            if self.isImmutablePolicy(pid):
                exists = True
            else:
                exists = self.policyEnabledFromFiles(pid)
            if not preserve_pending or pid not in self._desired_states:
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
            w.setData(Qt.ItemDataRole.UserRole, pid)
            w.setFlags(w.flags() | Qt.ItemFlag.ItemIsUserCheckable)
            w.setCheckState(Qt.CheckState.Checked if self._desired_states.get(pid, False) else Qt.CheckState.Unchecked)

            if self.isImmutablePolicy(pid):
                w.setToolTip(self.immutablePolicyText())
                w.setForeground(immutable_color)
            elif not self.isPolicyAvailable(pid):
                w.setFlags(w.flags() & ~Qt.ItemFlag.ItemIsUserCheckable)
                w.setToolTip(self.unavailablePolicyText(pid))
                w.setForeground(immutable_color)

            self.list.addItem(w)

        self._updating_checks = False

        if self.list.count() > 0:
            target_row = -1

            if self._current_id is not None:
                for i in range(self.list.count()):
                    it = self.list.item(i)
                    if it.data(Qt.ItemDataRole.UserRole) == self._current_id:
                        target_row = i
                        break

            if target_row < 0:
                for i in range(self.list.count()):
                    it = self.list.item(i)
                    if it.data(Qt.ItemDataRole.UserRole) == "hide-users":
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
            pid = it.data(Qt.ItemDataRole.UserRole)
            it.setCheckState(Qt.CheckState.Checked if self._desired_states.get(pid, False) else Qt.CheckState.Unchecked)

            if self.isImmutablePolicy(pid):
                it.setToolTip(self.immutablePolicyText())
                it.setForeground(immutable_color)
            elif not self.isPolicyAvailable(pid):
                it.setFlags(it.flags() & ~Qt.ItemFlag.ItemIsUserCheckable)
                it.setToolTip(self.unavailablePolicyText(pid))
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
        pid = it.data(Qt.ItemDataRole.UserRole)
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

        pid = it.data(Qt.ItemDataRole.UserRole)

        if self.isImmutablePolicy(pid):
            self._updating_checks = True
            it.setCheckState(Qt.CheckState.Checked)
            self._updating_checks = False
            self._desired_states[pid] = True
            self._last_states[pid] = True
            self.refreshApplyButton()
            return

        if not self.isPolicyAvailable(pid):
            self._updating_checks = True
            it.setCheckState(Qt.CheckState.Checked if self._last_states.get(pid, False) else Qt.CheckState.Unchecked)
            self._updating_checks = False
            self._desired_states[pid] = self._last_states.get(pid, False)
            self.refreshApplyButton()
            return

        self._desired_states[pid] = (it.checkState() == Qt.CheckState.Checked)
        self.refreshApplyButton()

    def appendLog(self, text):
        self.log.append(text)

    def selectedIds(self):
        ids = []
        for item in self._items:
            pid = item.get("id")
            if not self.isPolicyVisible(pid):
                continue
            if not self.isPolicyAvailable(pid):
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
            if not self.isPolicyAvailable(pid):
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
        p.setProcessChannelMode(QProcess.ProcessChannelMode.MergedChannels)
        completed = [False]

        def _finished(code, status, msgs=messages, proc=p):
            if completed[0]:
                return
            completed[0] = True
            output = bytes(proc.readAll()).decode("utf-8", errors="replace").strip()
            succeeded = code == 0 and status == QProcess.ExitStatus.NormalExit
            states = self.readPolicyStates()
            if msgs:
                for pid, title, mode, desired in msgs:
                    if succeeded or bool(states.get(pid, False)) == desired:
                        self.appendLog(title + " - " + mode)
            if not succeeded:
                if output:
                    self.appendLog(output)
                else:
                    self.appendLog(self.tr("Policies are not activated; authenticate to apply policies"))
                self.appendLog(self.tr("Policy changes may be partially applied. Check the system configuration."))
            self.syncStatesFromFiles(preserve_pending=not succeeded)
            self.setApplyInProgress(False)
            self.appendLog("")
            if proc in self.procs:
                self.procs.remove(proc)
            proc.deleteLater()

        def _error(error):
            if error == QProcess.ProcessError.FailedToStart:
                _finished(-1, QProcess.ExitStatus.CrashExit)

        p.finished.connect(_finished)
        p.errorOccurred.connect(_error)
        self.procs.append(p)
        p.start()

    def runUser(self, args):
        program = args[0]
        arguments = args[1:] if len(args) > 1 else []
        QProcess.startDetached(program, arguments)

    def cleanupLegacyPolicyMarkers(self):
        return (
            "set -e\n"
            "gdm_changed=0\n"
            "for dir in /etc/dconf/db/gdm.d /etc/lightdm/lightdm.conf.d /etc/sddm.conf.d; do\n"
            "    [ -d \"$dir\" ] || continue\n"
            "    for file in \"$dir\"/50-altcenter-*; do\n"
            "        [ -f \"$file\" ] && [ ! -L \"$file\" ] || continue\n"
            "        if [ \"$file\" = /etc/lightdm/lightdm.conf.d/50-altcenter-grub-hide-boot-menu.conf ] && [ ! -s \"$file\" ]; then\n"
            "            rm -f \"$file\"\n"
            "            continue\n"
            "        fi\n"
            "        if [ \"$file\" = /etc/lightdm/lightdm.conf.d/50-altcenter-no-username-autocomplete.conf ] && [ \"$(cat \"$file\")\" = \"enter-username=false\" ]; then\n"
            "            rm -f \"$file\"\n"
            "            continue\n"
            "        fi\n"
            "        name=${file##*/}\n"
            "        name=${name%.conf}\n"
            "        id=${name#50-altcenter-}\n"
            "        case \"$id\" in ''|*[!a-z0-9-]*) continue ;; esac\n"
            "        if awk -v id=\"$id\" '\n"
            "            BEGIN { valid=1; markers=0; uids=0 }\n"
            "            /^[[:space:]]*$/ { next }\n"
            "            $0 == \"policy:\" id { markers++; next }\n"
            "            id == \"deny-system-accounts\" && /^UID_MIN=[0-9]+$/ { uids++; next }\n"
            "            { valid=0 }\n"
            "            END { exit !(valid && markers == 1 && uids <= 1) }\n"
            "        ' \"$file\"; then\n"
            "            rm -f \"$file\"\n"
            "            if [ \"$dir\" = /etc/dconf/db/gdm.d ]; then gdm_changed=1; fi\n"
            "        elif awk -v id=\"$id\" '\n"
            "            NR == 1 { marker=($0 == \"policy:\" id); next }\n"
            "            NR == 2 {\n"
            "                if (id == \"deny-system-accounts\" && $0 ~ /^UID_MIN=[0-9]+$/) uid=1\n"
            "                else if (length($0) >= 3 && substr($0, 1, 1) == \"[\" && substr($0, length($0), 1) == \"]\") group=1\n"
            "                next\n"
            "            }\n"
            "            NR == 3 && uid && length($0) >= 3 && substr($0, 1, 1) == \"[\" && substr($0, length($0), 1) == \"]\" { group=1 }\n"
            "            END { exit !(marker && group) }\n"
            "        ' \"$file\"; then\n"
            "            if [ \"$id\" = deny-system-accounts ] && sed -n '2p' \"$file\" | grep -Eq '^UID_MIN=[0-9]+$'; then\n"
            "                sed -i '1,2d' \"$file\"\n"
            "            else\n"
            "                sed -i '1d' \"$file\"\n"
            "            fi\n"
            "            if [ \"$dir\" = /etc/dconf/db/gdm.d ]; then gdm_changed=1; fi\n"
            "        fi\n"
            "    done\n"
            "done\n"
            "if [ \"$gdm_changed\" -eq 1 ]; then\n"
            "    if command -v dconf >/dev/null 2>&1; then\n"
            "        dconf update\n"
            "    elif [ " + shlex.quote(self.active_dm) + " = gdm ]; then\n"
            "        echo 'dconf command not found' >&2\n"
            "        exit 1\n"
            "    fi\n"
            "fi"
        )

    def buildPolicyScript(self, pid, commands, dconf_required, state_data):
        state_path = self.expectedFiles("")[0]
        state_dir = os.path.dirname(state_path)
        script = [
            "set -e",
            "umask 022",
            "state_tmp=''",
            "trap 'if [ -n \"$state_tmp\" ]; then rm -f \"$state_tmp\"; fi' EXIT",
            "mkdir -p -m 755 " + shlex.quote(state_dir)
        ]
        for command in commands:
            script.append("sh -ec " + shlex.quote(command))
        if dconf_required:
            if self.active_dm == "gdm":
                script.append("command -v dconf >/dev/null 2>&1 || { echo 'dconf command not found' >&2; exit 1; }")
                script.append("dconf update")
            else:
                script.append("if command -v dconf >/dev/null 2>&1; then dconf update; fi")
        script.extend((
            "chown root:root " + shlex.quote(state_dir),
            "chmod 755 " + shlex.quote(state_dir),
            "state_tmp=$(mktemp " + shlex.quote(state_dir + "/.states.XXXXXXXX") + ")",
            "printf '%s\\n' " + shlex.quote(state_data) + " > \"$state_tmp\"",
            "chmod 644 \"$state_tmp\"",
            "mv -f \"$state_tmp\" " + shlex.quote(state_path),
            "state_tmp=''"
        ))
        return "; ".join(script)

    def applySelected(self):
        if self._apply_in_progress:
            return
        if not self.hasPendingChanges():
            self.refreshApplyButton()
            return
        if not self.log.isVisible():
            self.btn_toggle_console.click()

        dm = self.active_dm
        changes = []
        for item in self._items:
            pid = item.get("id")
            if not self.isPolicyVisible(pid) or not self.isPolicyAvailable(pid):
                continue
            if self.isImmutablePolicy(pid):
                self._desired_states[pid] = True
                self._last_states[pid] = True
                continue
            desired = self._desired_states.get(pid, False)
            if desired == self._last_states.get(pid, False):
                continue
            mode = "apply" if desired else "revert"
            status = self.tr("activated") if desired else self.tr("deactivated")
            commands = []
            dconf_required = False
            for step in item.get(mode, []):
                if step.get("type") != "cmd":
                    continue
                step_dm = step.get("dm", "any")
                if step_dm not in ("any", dm):
                    continue
                args = step.get("run", [])
                if not args:
                    continue
                if len(args) >= 3 and args[0] == "/bin/sh" and args[1] == "-c":
                    command = args[2]
                else:
                    command = " ".join(shlex.quote(part) for part in args)
                commands.append(command)
                if "/etc/dconf/db/" in command:
                    dconf_required = True
            if commands:
                changes.append((pid, self.loc(item, "title") or self.tr("Policy"), status, desired, commands, dconf_required))

        if not changes:
            self.syncStatesFromFiles()
            return
        try:
            states = self.readPolicyStates(strict=True)
        except (OSError, ValueError) as e:
            self.appendLog(str(e))
            self.refreshApplyButton()
            return
        saved_dm = states.get("__display_manager")
        if saved_dm and dm != "any" and saved_dm != dm:
            for item in self._items:
                pid = item.get("id")
                if self.policyUsesDisplayManager(pid):
                    states[pid] = False
        if dm != "any":
            states["__display_manager"] = dm
        scripts = []
        messages = []
        for pid, title, status, desired, commands, dconf_required in changes:
            states[pid] = desired
            state_data = json.dumps(states, ensure_ascii=False, sort_keys=True)
            script = self.buildPolicyScript(pid, commands, dconf_required, state_data)
            scripts.append("sh -ec " + shlex.quote(script))
            messages.append((pid, title, status, desired))
        self.apply_counter += 1
        self.appendLog(str(self.apply_counter) + " " + self.tr("apply"))
        self.setApplyInProgress(True)
        cleanup = "sh -ec " + shlex.quote(self.cleanupLegacyPolicyMarkers())
        self.runRoot(["/bin/sh", "-c", "set -e; " + " && ".join([cleanup] + scripts)], messages)

    def getReportData(self):
        result = []

        for item in self._items:
            pid = item.get("id")
            title = self.loc(item, "title")

            if self.isImmutablePolicy(pid):
                enabled = True
            else:
                enabled = self.policyEnabledFromFiles(pid)

            result.append({
                "name": title,
                "enabled": enabled
            })

        return result

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
