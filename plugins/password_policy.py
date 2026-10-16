import os
import re
import base64
import hashlib
import stat
import grp
from pathlib import Path
from typing import Dict, Any, Tuple, List

from PyQt6.QtCore import Qt, QProcess, QProcessEnvironment
from PyQt6.QtGui import QStandardItem, QFont
from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QFormLayout, QCheckBox, QSpinBox, QLabel,
    QHBoxLayout, QPushButton, QMessageBox, QStackedWidget, QListWidget,
    QListWidgetItem, QScrollArea, QFrame
)

import plugins


PAM_DIR = Path("/etc/pam.d")
PAM_PASSWD = PAM_DIR / "passwd"
PAM_PROTECTION = PAM_DIR / "system-auth.protection-alt"
PAM_SYSTEM_AUTH = PAM_DIR / "system-auth"
PAM_LOCAL_ONLY = PAM_DIR / "system-auth-local-only"
PASSWDQC_CONF = Path("/etc/passwdqc.conf")
GROUP_BEGIN = "# ALT Center group password policies begin"
GROUP_END = "# ALT Center group password policies end"
MAX_GROUP_POLICIES = 24


class PasswordWidget(QWidget):
    def __init__(self, palette=None):
        super().__init__()

        if palette:
            self.setPalette(palette)

        self.proc_apply = None
        self._module_kind = "none"
        self._managed_path = None
        self._original_text = ""
        self._original_hash = ""
        self._dependency_hashes = {}
        self._states: Dict[str, Dict[str, Any]] = {}
        self._drafts: Dict[str, Dict[str, Any]] = {}
        self._active_group = None
        self._read_error = ""
        self._loading = False
        self._can_write = False
        self._passwdqc_enforce_none = False

        self._build_ui()
        self._reload_groups()
        self._load()

    def _build_ui(self):
        root = QVBoxLayout(self)
        root.setContentsMargins(10, 10, 10, 10)
        root.setSpacing(10)

        self.scroll = QScrollArea()
        self.scroll.setWidgetResizable(True)
        self.scroll.setFrameShape(QFrame.Shape.NoFrame)
        self.scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        root.addWidget(self.scroll, 1)

        content = QWidget()
        v = QVBoxLayout(content)
        v.setContentsMargins(0, 0, 10, 0)
        v.setSpacing(10)

        self.lbl_module = QLabel("")
        self.lbl_module.setWordWrap(True)
        v.addWidget(self.lbl_module)

        self.list_groups = QListWidget()
        self.list_groups.setSelectionMode(QListWidget.SelectionMode.MultiSelection)
        self.list_groups.setMinimumHeight(190)
        self.list_groups.setMaximumHeight(280)
        v.addWidget(self.list_groups)

        self.lbl_active = QLabel(self.tr("Active group: Not selected"))
        f = QFont()
        f.setBold(True)
        self.lbl_active.setFont(f)
        self.lbl_active.setWordWrap(True)
        v.addWidget(self.lbl_active)

        form = QFormLayout()
        form.setLabelAlignment(Qt.AlignmentFlag.AlignLeft)
        form.setFormAlignment(Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignTop)
        form.setVerticalSpacing(8)
        form.setHorizontalSpacing(16)
        form.setFieldGrowthPolicy(QFormLayout.FieldGrowthPolicy.FieldsStayAtSizeHint)

        self.sp_min = QSpinBox()
        self.sp_min.setRange(6, 128)
        self.sp_min.setKeyboardTracking(False)
        self.sp_min.setAccelerated(True)

        self.sp_difok = QSpinBox()
        self.sp_difok.setRange(0, 128)
        self.sp_difok.setKeyboardTracking(False)

        self.sp_l = QSpinBox()
        self.sp_l.setRange(0, 16)
        self.sp_l.setKeyboardTracking(False)

        self.sp_u = QSpinBox()
        self.sp_u.setRange(0, 16)
        self.sp_u.setKeyboardTracking(False)

        self.sp_d = QSpinBox()
        self.sp_d.setRange(0, 16)
        self.sp_d.setKeyboardTracking(False)

        self.sp_o = QSpinBox()
        self.sp_o.setRange(0, 16)
        self.sp_o.setKeyboardTracking(False)

        self.sp_remember = QSpinBox()
        self.sp_remember.setRange(1, 10)
        self.sp_remember.setKeyboardTracking(False)

        self.sp_retry = QSpinBox()
        self.sp_retry.setRange(2, 5)
        self.sp_retry.setKeyboardTracking(False)

        for widget in (self.sp_min, self.sp_difok, self.sp_l, self.sp_u,
                       self.sp_d, self.sp_o, self.sp_remember, self.sp_retry):
            widget.setMinimumWidth(125)

        self.chk_user = QCheckBox(self.tr("Check username"))
        self.chk_gecos = QCheckBox(self.tr("Check GECOS"))
        self.chk_dict = QCheckBox(self.tr("Dictionary check"))
        self.chk_root = QCheckBox(self.tr("Enforce for root"))
        self.chk_history_root = QCheckBox(self.tr("Enforce password history for root"))

        form.addRow(self.tr("Minimum password length"), self.sp_min)
        form.addRow(self.tr("Minimum changed characters"), self.sp_difok)
        form.addRow(self.tr("Minimum lowercase"), self.sp_l)
        form.addRow(self.tr("Minimum uppercase"), self.sp_u)
        form.addRow(self.tr("Minimum digits"), self.sp_d)
        form.addRow(self.tr("Minimum other characters"), self.sp_o)
        form.addRow(self.tr("Password input attempts (retry)"), self.sp_retry)
        form.addRow(self.tr("Forbid reuse of last N passwords"), self.sp_remember)
        form.addRow(self.chk_user)
        form.addRow(self.chk_gecos)
        form.addRow(self.chk_dict)
        form.addRow(self.chk_root)
        form.addRow(self.chk_history_root)
        v.addLayout(form)
        v.addStretch(1)
        self.scroll.setWidget(content)

        self.lbl_status = QLabel("")
        self.lbl_status.setWordWrap(True)
        self.lbl_status.setTextInteractionFlags(Qt.TextInteractionFlag.TextSelectableByMouse)
        root.addWidget(self.lbl_status)

        btns = QHBoxLayout()
        self.btn_apply = QPushButton(self.tr("Apply"))
        self.btn_reset = QPushButton(self.tr("Reset"))
        btns.addWidget(self.btn_apply)
        btns.addWidget(self.btn_reset)
        btns.addStretch(1)
        root.addLayout(btns)

        self.btn_apply.clicked.connect(self._on_apply)
        self.btn_reset.clicked.connect(self._on_reset)
        self.list_groups.itemSelectionChanged.connect(self._on_groups_selection_changed)

        for widget in (self.sp_min, self.sp_difok, self.sp_l, self.sp_u, self.sp_d,
                       self.sp_o, self.sp_remember, self.sp_retry):
            widget.valueChanged.connect(self._on_form_changed)

        for widget in (self.chk_user, self.chk_gecos, self.chk_dict,
                       self.chk_root, self.chk_history_root):
            widget.stateChanged.connect(self._on_form_changed)

    def _read_file(self, path):
        try:
            if path.is_symlink() or not path.is_file():
                return None
            return path.read_text(encoding="utf-8")
        except (OSError, UnicodeError):
            return None

    def _uid_min(self):
        try:
            text = Path("/etc/login.defs").read_text(encoding="utf-8", errors="replace")
            found = re.search(r"^\s*GID_MIN\s+(\d+)\s*$", text, re.MULTILINE)
            if found:
                return int(found.group(1))
        except OSError:
            pass
        return 1000

    def _reload_groups(self):
        self.list_groups.blockSignals(True)
        self.list_groups.clear()
        item = QListWidgetItem(self.tr("All groups"))
        item.setData(Qt.ItemDataRole.UserRole, "*ALL*")
        self.list_groups.addItem(item)

        try:
            gid_min = self._uid_min()
            groups = []
            with open("/etc/group", "r", encoding="utf-8", errors="replace") as stream:
                for line in stream:
                    fields = line.strip().split(":")
                    if len(fields) >= 3 and fields[2].isdigit():
                        if int(fields[2]) >= gid_min:
                            groups.append((fields[0], int(fields[2])))

            for name, gid in sorted(groups, key=lambda group: (group[1], group[0])):
                item = QListWidgetItem(f"{name} (gid {gid})")
                item.setData(Qt.ItemDataRole.UserRole, name)
                self.list_groups.addItem(item)
        except OSError:
            pass

        self.list_groups.item(0).setSelected(True)
        self.list_groups.scrollToItem(self.list_groups.item(0))
        self.list_groups.blockSignals(False)
        self._active_group = "*ALL*"

    def _password_lines(self, text):
        lines = []
        for line in text.splitlines():
            value = line.strip()
            if not value or value.startswith("#"):
                continue
            if re.match(r"^password\s+", value, re.IGNORECASE):
                lines.append(value)
        return lines

    def _check_managed_chain(self):
        text = self._read_file(PAM_PASSWD)
        if text is None:
            return False
        commands = self._password_lines(text)
        return len(commands) == 1 and bool(re.fullmatch(
            r"password\s+include\s+system-auth\.protection-alt", commands[0], re.IGNORECASE
        ))

    def _check_passwdqc_chain(self):
        text = self._read_file(PAM_PASSWD)
        if text is None:
            return False
        commands = self._password_lines(text)
        if len(commands) != 1:
            return False
        command = commands[0]
        if re.fullmatch(r"password\s+include\s+system-auth", command, re.IGNORECASE):
            system = self._read_file(PAM_SYSTEM_AUTH)
            if system is None:
                return False
            if not any(re.fullmatch(r"password\s+include\s+system-auth-local-only", line, re.IGNORECASE)
                       for line in self._password_lines(system)):
                return False
        elif not re.fullmatch(r"password\s+include\s+system-auth-local-only", command, re.IGNORECASE):
            return False

        local = self._read_file(PAM_LOCAL_ONLY)
        if local is None:
            return False
        quality = [line for line in self._password_lines(local) if "pam_passwdqc.so" in line]
        tokens = quality[0].split() if len(quality) == 1 else []
        if not tokens or "config=/etc/passwdqc.conf" not in tokens:
            return False
        self._passwdqc_enforce_none = "enforce=none" in tokens
        return True

    def _get_pwquality_config(self):
        values = {}
        paths = [Path("/etc/security/pwquality.conf")]
        folder = Path("/etc/security/pwquality.conf.d")
        if folder.is_dir():
            paths.extend(sorted(folder.glob("*.conf")))
        for path in paths:
            text = self._read_file(path)
            if text is None:
                continue
            for line in text.splitlines():
                value = line.split("#", 1)[0].strip()
                match = re.fullmatch(r"([A-Za-z_]+)\s*=\s*(\S+)", value)
                if match:
                    values[match.group(1).lower()] = match.group(2)
                elif value == "enforce_for_root":
                    values["enforce_for_root"] = "1"
        return values

    def _decode_pwquality(self, quality, history):
        options = self._get_pwquality_config()
        for token in quality.split()[3:]:
            if "=" in token:
                name, value = token.split("=", 1)
                options[name.lower()] = value
            elif token == "enforce_for_root":
                options["enforce_for_root"] = "1"
        for token in quality.split()[3:]:
            if token == "enforce_for_root=0":
                options["enforce_for_root"] = "0"

        history_parts = history.split()[3:]
        history_options = {}
        for token in history_parts:
            if "=" in token:
                name, value = token.split("=", 1)
                history_options[name.lower()] = value

        def number(name, default):
            try:
                return int(options.get(name, default))
            except (TypeError, ValueError):
                return default

        def historic(name, default):
            try:
                return int(history_options.get(name, default))
            except (TypeError, ValueError):
                return default

        return {
            "minlen": number("minlen", 8),
            "difok": number("difok", 3),
            "req_l": max(0, -number("lcredit", 0)),
            "req_u": max(0, -number("ucredit", 0)),
            "req_d": max(0, -number("dcredit", 0)),
            "req_o": max(0, -number("ocredit", 0)),
            "retry": number("retry", 3),
            "remember": historic("remember", 5),
            "usercheck": number("usercheck", 1) != 0,
            "gecoscheck": number("gecoscheck", 0) != 0,
            "dictcheck": number("dictcheck", 1) != 0,
            "root_enforce": str(options.get("enforce_for_root", "0")).lower() not in ("0", "false", "no"),
            "history_root": "enforce_for_root" in history_parts or "enforce_for_root=1" in history_parts
        }

    def _managed_profile(self, text):
        lines = self._password_lines(text)
        if GROUP_BEGIN not in text and GROUP_END not in text:
            if len(lines) != 3:
                return None
            quality, history, tcb = lines
            if not self._valid_pair(quality, history):
                return None
            if not self._valid_tcb(tcb):
                return None
            if self._get_pwquality_config().get("enforcing") == "0":
                return None
            return self._decode_pwquality(quality, history), {}

        source = text.splitlines()
        begin_positions = [i for i, line in enumerate(source) if line.strip() == GROUP_BEGIN]
        end_positions = [i for i, line in enumerate(source) if line.strip() == GROUP_END]
        if len(begin_positions) != 1 or len(end_positions) != 1:
            return None
        begin = begin_positions[0]
        end = end_positions[0]
        if begin >= end:
            return None
        block = [line.strip() for line in source[begin + 1:end]]
        if len(block) < 2 or (len(block) - 2) % 4 != 0:
            return None
        group_count = (len(block) - 2) // 4
        if group_count < 1 or group_count > MAX_GROUP_POLICIES:
            return None
        outside = "\n".join(source[:begin] + source[end + 1:])
        outside_commands = self._password_lines(outside)
        if len(outside_commands) != 1 or not self._valid_tcb(outside_commands[0]):
            return None
        if len(lines) != group_count * 4 + 3:
            return None
        fallback_quality, fallback_history = block[-2:]
        if not self._valid_pair(fallback_quality, fallback_history):
            return None
        if self._get_pwquality_config().get("enforcing") == "0":
            return None

        stored_groups = {}
        previous = ""
        for index in range(group_count):
            gate, quality, history, exit_gate = block[index * 4:index * 4 + 4]
            match = re.fullmatch(
                r"password\s+\[success=ignore auth_err=3 default=die\]\s+"
                r"pam_succeed_if\.so quiet user ingroup ([A-Za-z_][A-Za-z0-9_.-]*)",
                gate
            )
            if not match:
                return None
            name = match.group(1)
            if name <= previous or not self._valid_group_name(name):
                return None
            previous = name
            if not self._valid_pair(quality, history):
                return None
            expected_skip = (group_count - index - 1) * 4 + 2
            if exit_gate != (f"password [success={expected_skip} default=die] "
                             f"pam_succeed_if.so quiet user ingroup {name}"):
                return None
            stored_groups[name] = self._decode_pwquality(quality, history)

        if not self._module_exists("pam_succeed_if.so"):
            return None
        return self._decode_pwquality(fallback_quality, fallback_history), stored_groups

    def _valid_pair(self, quality, history):
        return (bool(re.match(r"^password\s+requisite\s+pam_pwquality\.so(?:\s|$)", quality)) and
                bool(re.match(r"^password\s+requisite\s+pam_pwhistory\.so(?:\s|$)", history)) and
                "use_authtok" in history.split()[3:])

    def _valid_tcb(self, line):
        return bool(re.match(r"^password\s+required\s+pam_tcb\.so\s+use_authtok(?:\s|$)", line))

    def _valid_group_name(self, name):
        return bool(re.fullmatch(r"[A-Za-z_][A-Za-z0-9_.-]*", name))

    def _passwdqc_profile(self, text):
        lines = [line for line in text.splitlines() if re.match(r"^\s*min\s*=", line)]
        if len(lines) != 1:
            return None
        match = re.fullmatch(r"\s*min\s*=\s*(\d+),(\d+),(\d+),(\d+),(\d+)\s*", lines[0])
        if not match:
            return None
        values = [int(value) for value in match.groups()]
        if len(set(values)) != 1 or values[0] < 6 or values[0] > 72:
            return None
        return {
            "minlen": values[0],
            "difok": 0,
            "req_l": 0,
            "req_u": 0,
            "req_d": 0,
            "req_o": 0,
            "retry": 3,
            "remember": 5,
            "usercheck": False,
            "gecoscheck": False,
            "dictcheck": False,
            "root_enforce": False,
            "history_root": False
        }

    def _protected_file(self, path):
        try:
            info = path.stat()
            return (not path.is_symlink() and stat.S_ISREG(info.st_mode) and
                    info.st_uid == 0 and not (info.st_mode & 0o022))
        except OSError:
            return False

    def _capture_dependencies(self):
        paths = [PAM_PASSWD]
        if self._module_kind == "pwquality":
            base = Path("/etc/security/pwquality.conf")
            if base.exists():
                paths.append(base)
            folder = Path("/etc/security/pwquality.conf.d")
            if folder.is_dir():
                paths.extend(sorted(folder.glob("*.conf")))
        if self._module_kind == "passwdqc":
            paths.append(PAM_LOCAL_ONLY)
            text = self._read_file(PAM_PASSWD) or ""
            if any(re.fullmatch(r"password\s+include\s+system-auth", command, re.IGNORECASE)
                   for command in self._password_lines(text)):
                paths.append(PAM_SYSTEM_AUTH)
        result = {}
        for path in paths:
            text = self._read_file(path)
            if text is None or not self._protected_file(path):
                return None
            result[path] = hashlib.sha256(text.encode("utf-8")).hexdigest()
        return result

    def _state_in_range(self, state):
        return (6 <= state["minlen"] <= 128 and
                0 <= state["difok"] <= 128 and
                2 <= state["retry"] <= 5 and
                1 <= state["remember"] <= 10 and
                all(0 <= state[key] <= 16 for key in ("req_l", "req_u", "req_d", "req_o")))

    def _module_exists(self, name):
        return any((Path(folder) / name).is_file() for folder in ("/lib64/security", "/usr/lib64/security"))

    def _load(self, preserve_selection=False):
        selected = self._selected_groups() if preserve_selection else ["*ALL*"]
        self._loading = True
        self._can_write = False
        self._module_kind = "none"
        self._managed_path = None
        self._original_text = ""
        self._original_hash = ""
        self._dependency_hashes = {}
        self._read_error = ""
        self._states = {}
        self._drafts = {}
        self._passwdqc_enforce_none = False

        state = None
        groups = {}
        if self._check_managed_chain():
            self._module_kind = "pwquality"
            self._managed_path = PAM_PROTECTION
            text = self._read_file(self._managed_path)
            if text is not None:
                profile = self._managed_profile(text)
                if profile is not None:
                    state, groups = profile
                self._original_text = text
            self._can_write = (state is not None and self._protected_file(self._managed_path) and
                               self._state_in_range(state) and
                               all(self._state_in_range(value) for value in groups.values()) and
                               all(self._module_exists(name)
                               for name in ("pam_pwquality.so", "pam_pwhistory.so", "pam_tcb.so")))
            if self._can_write and groups:
                known = self._system_group_names()
                visible = {self.list_groups.item(i).data(Qt.ItemDataRole.UserRole)
                           for i in range(self.list_groups.count())}
                if known is None or any(name not in known or name not in visible for name in groups):
                    self._can_write = False
            if not self._can_write:
                self._read_error = self.tr("The existing PAM configuration is not supported for safe modification.")
        elif self._check_passwdqc_chain():
            self._module_kind = "passwdqc"
            self._managed_path = PASSWDQC_CONF
            text = self._read_file(self._managed_path)
            if text is not None:
                state = self._passwdqc_profile(text)
                self._original_text = text
            self._can_write = (state is not None and self._protected_file(self._managed_path) and
                               self._module_exists("pam_passwdqc.so"))
            if not self._can_write:
                self._read_error = self.tr("The passwdqc configuration has an unsupported format.")
        else:
            self._read_error = self.tr("The active PAM password configuration was not recognized. No system files will be changed.")

        if self._can_write:
            dependencies = self._capture_dependencies()
            if dependencies is None:
                self._can_write = False
                self._read_error = self.tr("Active PAM files could not be safely verified.")
            else:
                self._dependency_hashes = dependencies

        if state is None:
            state = self._default_state()
        self._states["*ALL*"] = dict(state)
        self._states.update(groups)
        self._drafts = {key: dict(value) for key, value in self._states.items()}
        self._original_hash = hashlib.sha256(self._original_text.encode("utf-8")).hexdigest()

        self.list_groups.blockSignals(True)
        self.list_groups.clearSelection()
        for i in range(self.list_groups.count()):
            item = self.list_groups.item(i)
            if item.data(Qt.ItemDataRole.UserRole) in selected:
                item.setSelected(True)
        self.list_groups.blockSignals(False)
        self._active_group = None
        self._loading = False
        self._on_groups_selection_changed()
        self._update_controls_enabled()
        self._update_apply_button()

    def _system_group_names(self):
        try:
            return {item.gr_name for item in grp.getgrall()}
        except (OSError, KeyError):
            return None

    def _default_state(self):
        return {
            "minlen": 8,
            "difok": 3,
            "req_l": 0,
            "req_u": 0,
            "req_d": 0,
            "req_o": 0,
            "retry": 3,
            "remember": 5,
            "usercheck": True,
            "gecoscheck": True,
            "dictcheck": True,
            "root_enforce": False,
            "history_root": True
        }

    def _state_from_form(self):
        return {
            "minlen": self.sp_min.value(),
            "difok": self.sp_difok.value(),
            "req_l": self.sp_l.value(),
            "req_u": self.sp_u.value(),
            "req_d": self.sp_d.value(),
            "req_o": self.sp_o.value(),
            "retry": self.sp_retry.value(),
            "remember": self.sp_remember.value(),
            "usercheck": self.chk_user.isChecked(),
            "gecoscheck": self.chk_gecos.isChecked(),
            "dictcheck": self.chk_dict.isChecked(),
            "root_enforce": self.chk_root.isChecked(),
            "history_root": self.chk_history_root.isChecked()
        }

    def _apply_state_to_form(self, state):
        old = self._loading
        self._loading = True
        self.sp_min.setValue(state["minlen"])
        self.sp_difok.setValue(state["difok"])
        self.sp_l.setValue(state["req_l"])
        self.sp_u.setValue(state["req_u"])
        self.sp_d.setValue(state["req_d"])
        self.sp_o.setValue(state["req_o"])
        self.sp_retry.setValue(state["retry"])
        self.sp_remember.setValue(state["remember"])
        self.chk_user.setChecked(state["usercheck"])
        self.chk_gecos.setChecked(state["gecoscheck"])
        self.chk_dict.setChecked(state["dictcheck"])
        self.chk_root.setChecked(state["root_enforce"])
        self.chk_history_root.setChecked(state["history_root"])
        self._loading = old

    def _selected_groups(self):
        keys = [item.data(Qt.ItemDataRole.UserRole) for item in self.list_groups.selectedItems()]
        if "*ALL*" in keys:
            return ["*ALL*"]
        return [key for key in keys if key]

    def _on_groups_selection_changed(self):
        if self._loading:
            return
        self._loading = True
        keys = self._selected_groups()
        if "*ALL*" in keys and len(self.list_groups.selectedItems()) > 1:
            self.list_groups.blockSignals(True)
            current = self.list_groups.currentItem()
            current_key = current.data(Qt.ItemDataRole.UserRole) if current else None
            if current_key == "*ALL*":
                for i in range(1, self.list_groups.count()):
                    self.list_groups.item(i).setSelected(False)
            else:
                self.list_groups.item(0).setSelected(False)
            self.list_groups.blockSignals(False)
            keys = self._selected_groups()

        if not keys:
            self._active_group = None
            self.lbl_active.setText(self.tr("Active group: Not selected"))
        else:
            current = self.list_groups.currentItem()
            current_key = current.data(Qt.ItemDataRole.UserRole) if current else None
            self._active_group = current_key if current_key in keys else keys[0]
            self.lbl_active.setText(self.tr("Active group: ") + ", ".join(
                self.tr("All groups") if key == "*ALL*" else key for key in keys
            ))
            state = self._drafts.get(self._active_group, self._drafts["*ALL*"])
            self._apply_state_to_form(state)
        self._loading = False
        self._update_controls_enabled()
        self._update_apply_button()

    def _on_form_changed(self, *args):
        if self._loading:
            return
        state = self._state_from_form()
        for key in self._selected_groups():
            self._drafts[key] = dict(state)
        self._update_apply_button()

    def _update_controls_enabled(self):
        selected = bool(self._selected_groups())
        editable = self._can_write and selected
        pwquality = self._module_kind == "pwquality"
        is_global = self._selected_groups() == ["*ALL*"]
        self.sp_min.setEnabled(editable and (pwquality or is_global))
        for widget in (self.sp_difok, self.sp_l, self.sp_u, self.sp_d, self.sp_o,
                       self.sp_retry, self.sp_remember, self.chk_user, self.chk_gecos,
                       self.chk_dict, self.chk_root, self.chk_history_root):
            widget.setEnabled(editable and pwquality)

        self.btn_reset.setEnabled(editable and (pwquality or is_global))

        if self._module_kind == "pwquality":
            self.lbl_module.setText(self.tr("Active module: pam_pwquality (ALT Protection profile)"))
        elif self._module_kind == "passwdqc":
            self.lbl_module.setText(self.tr("Active module: pam_passwdqc (minimum length only)"))
        else:
            self.lbl_module.setText(self.tr("Active module: unknown"))

        if self._read_error:
            self.lbl_status.setText(self._read_error)
        elif self._module_kind == "passwdqc" and not is_global and selected:
            self.lbl_status.setText(self.tr("Separate group policies require an active pam_pwquality profile."))
        elif self._passwdqc_enforce_none:
            self.lbl_status.setText(self.tr("pam_passwdqc currently uses enforce=none. Password strength may not be enforced."))
        elif pwquality and len(self._states) > 1:
            self.lbl_status.setText(self.tr("When users belong to several groups, the first matching group in alphabetical order takes precedence."))
        else:
            self.lbl_status.setText("")

    def _update_apply_button(self):
        running = self.proc_apply is not None and self.proc_apply.state() != QProcess.ProcessState.NotRunning
        keys = self._selected_groups()
        if not keys or not self._can_write or running:
            self.btn_apply.setEnabled(False)
            return
        if self._module_kind == "passwdqc":
            changed = keys == ["*ALL*"] and self._drafts["*ALL*"]["minlen"] != self._states["*ALL*"]["minlen"]
            self.btn_apply.setEnabled(changed)
            return
        changed = any(state != self._states.get(key, self._states["*ALL*"])
                      for key, state in self._drafts.items())
        self.btn_apply.setEnabled(changed)

    def _validate(self, state):
        if not 6 <= state["minlen"] <= (72 if self._module_kind == "passwdqc" else 128):
            return False, self.tr("Invalid minimum password length.")
        if self._module_kind == "pwquality":
            if state["difok"] > state["minlen"]:
                return False, self.tr("Minimum changed characters exceeds minimum length.")
            if sum(state[name] for name in ("req_l", "req_u", "req_d", "req_o")) > state["minlen"]:
                return False, self.tr("Sum of required character classes exceeds minimum length.")
        return True, ""

    def _quality_line(self, template, state):
        options = ("retry", "minlen", "difok", "lcredit", "ucredit", "dcredit",
                   "ocredit", "usercheck", "gecoscheck", "dictcheck", "enforce_for_root")
        tokens = template.strip().split()
        saved = [token for token in tokens[3:] if token.split("=", 1)[0] not in options]
        added = [
            f"retry={state['retry']}",
            f"minlen={state['minlen']}",
            f"difok={state['difok']}",
            f"lcredit={-state['req_l']}",
            f"ucredit={-state['req_u']}",
            f"dcredit={-state['req_d']}",
            f"ocredit={-state['req_o']}",
            f"usercheck={int(state['usercheck'])}",
            f"gecoscheck={int(state['gecoscheck'])}",
            f"dictcheck={int(state['dictcheck'])}"
        ]
        if state["root_enforce"]:
            added.append("enforce_for_root")
        elif "enforce_for_root=0" in tokens[3:]:
            added.append("enforce_for_root=0")
        return "password   requisite                     pam_pwquality.so " + " ".join(saved + added)

    def _history_line(self, template, state):
        tokens = template.strip().split()
        saved = [token for token in tokens[3:]
                 if token.split("=", 1)[0] not in ("remember", "enforce_for_root")]
        if "use_authtok" not in saved:
            return None
        added = [f"remember={state['remember']}"]
        if state["history_root"]:
            added.append("enforce_for_root")
        return "password   requisite                     pam_pwhistory.so " + " ".join(saved + added)

    def _render_pwquality(self, text, state):
        lines = text.splitlines(keepends=True)
        result = []
        quality_count = 0
        history_count = 0
        for line in lines:
            stripped = line.strip()
            if re.match(r"^password\s+requisite\s+pam_pwquality\.so(?:\s|$)", stripped):
                quality_count += 1
                result.append(self._quality_line(stripped, state) + ("\n" if line.endswith("\n") else ""))
            elif re.match(r"^password\s+requisite\s+pam_pwhistory\.so(?:\s|$)", stripped):
                history_count += 1
                changed = self._history_line(stripped, state)
                if changed is None:
                    return None
                result.append(changed + ("\n" if line.endswith("\n") else ""))
            else:
                result.append(line)
        if quality_count != 1 or history_count != 1:
            return None
        return "".join(result)

    def _render_group_block(self, default, groups, quality_template, history_template):
        ordered = sorted(groups)
        if not ordered or len(ordered) > MAX_GROUP_POLICIES:
            return None
        lines = [GROUP_BEGIN]
        for index, name in enumerate(ordered):
            if not self._valid_group_name(name):
                return None
            state = groups[name]
            lines.append(f"password [success=ignore auth_err=3 default=die] pam_succeed_if.so quiet user ingroup {name}")
            lines.append(self._quality_line(quality_template, state))
            history = self._history_line(history_template, state)
            if history is None:
                return None
            lines.append(history)
            skip = (len(ordered) - index - 1) * 4 + 2
            lines.append(f"password [success={skip} default=die] pam_succeed_if.so quiet user ingroup {name}")
        lines.append(self._quality_line(quality_template, default))
        history = self._history_line(history_template, default)
        if history is None:
            return None
        lines.append(history)
        lines.append(GROUP_END)
        return "\n".join(lines) + "\n"

    def _render_with_groups(self, text, default, groups):
        source = text.splitlines(keepends=True)
        old_begin = next((i for i, line in enumerate(source) if line.strip() == GROUP_BEGIN), None)
        old_end = next((i for i, line in enumerate(source) if line.strip() == GROUP_END), None)
        if old_begin is not None or old_end is not None:
            if old_begin is None or old_end is None or old_begin >= old_end:
                return None
            existing = [line.strip() for line in source[old_begin + 1:old_end]]
            if len(existing) < 2:
                return None
            quality_template, history_template = existing[-2:]
            if not self._valid_pair(quality_template, history_template):
                return None
            if groups:
                block = self._render_group_block(default, groups, quality_template, history_template)
                return "".join(source[:old_begin]) + block + "".join(source[old_end + 1:]) if block else None
            return "".join(source[:old_begin]) + self._quality_line(quality_template, default) + "\n" + \
                   self._history_line(history_template, default) + "\n" + "".join(source[old_end + 1:])

        quality_indexes = [i for i, line in enumerate(source) if re.match(
            r"^password\s+requisite\s+pam_pwquality\.so(?:\s|$)", line.strip())]
        history_indexes = [i for i, line in enumerate(source) if re.match(
            r"^password\s+requisite\s+pam_pwhistory\.so(?:\s|$)", line.strip())]
        if len(quality_indexes) != 1 or len(history_indexes) != 1:
            return None
        qi = quality_indexes[0]
        hi = history_indexes[0]
        if hi != qi + 1:
            return None
        if not groups:
            return self._render_pwquality(text, default)
        block = self._render_group_block(default, groups, source[qi].strip(), source[hi].strip())
        return "".join(source[:qi]) + block + "".join(source[hi + 1:]) if block else None

    def _render_passwdqc(self, text, state):
        replacement = f"min={','.join([str(state['minlen'])] * 5)}"
        new, count = re.subn(r"^[ \t]*min[ \t]*=[ \t]*\d+,\d+,\d+,\d+,\d+[ \t]*$",
                             replacement, text, flags=re.MULTILINE)
        return new if count == 1 else None

    def _create_command(self, original, updated, path):
        if path not in (PAM_PROTECTION, PASSWDQC_CONF):
            return None

        payload = base64.b64encode(updated.encode("utf-8")).decode("ascii")
        if len(payload) > 100000:
            return None

        old_hash = hashlib.sha256(original.encode("utf-8")).hexdigest()
        new_hash = hashlib.sha256(updated.encode("utf-8")).hexdigest()

        checks = ""
        for dependency, fingerprint in self._dependency_hashes.items():
            checks += (
                f"test -f '{dependency}' && test ! -L '{dependency}'\n"
                f"test \"$(sha256sum '{dependency}' | cut -d ' ' -f 1)\" = '{fingerprint}' || "
                "{ echo 'Active PAM chain changed externally' >&2; exit 26; }\n"
            )

        return (
            "set -eu\n"
            "export LC_ALL=C\n"
            "umask 077\n"
            f"file='{path}'\n"
            f"expected='{old_hash}'\n"
            f"result='{new_hash}'\n"
            f"payload='{payload}'\n"
            "test \"$(id -u)\" -eq 0\n"
            "test -f \"$file\" && test ! -L \"$file\"\n"
            "test \"$(stat -c %u \"$file\")\" -eq 0\n"
            "test -z \"$(find \"$file\" -maxdepth 0 -perm /022 -print)\"\n"
            "dir=$(dirname \"$file\")\n"
            "test \"$(stat -c %u \"$dir\")\" -eq 0\n"
            "test -z \"$(find \"$dir\" -maxdepth 0 -perm /022 -print)\"\n"
            f"{checks}"
            "test \"$(sha256sum \"$file\" | cut -d ' ' -f 1)\" = \"$expected\" || "
            "{ echo 'Configuration changed externally' >&2; exit 24; }\n"
            "tmp=$(mktemp \"$dir/.altcenter-pam.XXXXXXXX\")\n"
            "backup=\"$dir/$(basename \"$file\").altcenter-$(date +%Y-%m-%d_%H-%M-%S).bak\"\n"
            "new_backup=1\n"
            "if [ -e \"$backup\" ] || [ -L \"$backup\" ]; then\n"
            "    test -f \"$backup\" && test ! -L \"$backup\"\n"
            "    test \"$(stat -c %u \"$backup\")\" -eq 0\n"
            "    new_backup=0\n"
            "fi\n"
            "swapped=0\n"
            "trap 'rc=$?; rm -f -- \"$tmp\"; "
            "if [ \"$rc\" -ne 0 ]; then "
            "if [ \"$swapped\" -eq 1 ]; then "
            "if cp -a -- \"$backup\" \"$file\" && "
            "test \"$(sha256sum \"$file\" | cut -d \" \" -f 1)\" = \"$expected\"; then "
            "if [ \"$new_backup\" -eq 1 ]; then rm -f -- \"$backup\"; fi; "
            "else echo \"Rollback failed. Backup: $backup\" >&2; fi; "
            "elif [ \"$new_backup\" -eq 1 ]; then rm -f -- \"$backup\"; fi; "
            "fi; exit \"$rc\"' EXIT\n"
            "cp -a -- \"$file\" \"$tmp\"\n"
            "printf '%s' \"$payload\" | base64 -d > \"$tmp\"\n"
            "test \"$(sha256sum \"$tmp\" | cut -d ' ' -f 1)\" = \"$result\"\n"
            "cp -a -- \"$file\" \"$backup\"\n"
            "test \"$(sha256sum \"$file\" | cut -d ' ' -f 1)\" = \"$expected\" || "
            "{ echo 'Configuration changed externally' >&2; exit 25; }\n"
            "mv -f -- \"$tmp\" \"$file\"\n"
            "swapped=1\n"
            "test \"$(sha256sum \"$file\" | cut -d ' ' -f 1)\" = \"$result\"\n"
            "set -- \"$dir/$(basename \"$file\")\".altcenter-*.bak\n"
            "while [ \"$#\" -gt 5 ]; do rm -f -- \"$1\"; shift; done\n"
            "echo \"Backup: $backup (up to 5 dated copies per file in $dir)\"\n"
        )

    def _on_apply(self):
        if not self._can_write or not self._selected_groups():
            return
        if self.proc_apply is not None and self.proc_apply.state() != QProcess.ProcessState.NotRunning:
            return

        baseline = self._drafts["*ALL*"]
        groups = {}
        if self._module_kind == "pwquality":
            known_groups = self._system_group_names()
            if known_groups is None:
                QMessageBox.critical(self, self.tr("Error"), self.tr("Could not verify system groups."))
                return
            for key, state in self._drafts.items():
                if key == "*ALL*" or state == baseline:
                    continue
                if key not in known_groups or not self._valid_group_name(key):
                    QMessageBox.critical(self, self.tr("Error"), self.tr("Invalid group name or missing system group."))
                    return
                groups[key] = state
            if len(groups) > MAX_GROUP_POLICIES:
                QMessageBox.warning(self, self.tr("Error"), self.tr("Too many group policies."))
                return
            if groups and not self._module_exists("pam_succeed_if.so"):
                QMessageBox.critical(self, self.tr("Error"), self.tr("Required PAM module pam_succeed_if.so is missing."))
                return
            for state in [baseline, *groups.values()]:
                ok, message = self._validate(state)
                if not ok:
                    QMessageBox.warning(self, self.tr("Parameter validation"), message)
                    return
            updated = self._render_with_groups(self._original_text, baseline, groups)
        elif self._module_kind == "passwdqc":
            if self._selected_groups() != ["*ALL*"]:
                return
            ok, message = self._validate(baseline)
            if not ok:
                QMessageBox.warning(self, self.tr("Parameter validation"), message)
                return
            updated = self._render_passwdqc(self._original_text, baseline)
        else:
            return

        if updated is None:
            QMessageBox.critical(self, self.tr("Error"), self.tr("Failed to prepare safe changes."))
            return
        if updated == self._original_text:
            self._update_apply_button()
            return

        if self._module_kind == "pwquality":
            verified = self._managed_profile(updated)
            if verified is None:
                QMessageBox.critical(self, self.tr("Error"), self.tr("The prepared PAM profile did not pass validation."))
                return
            parsed_baseline, parsed_groups = verified
            if parsed_baseline != baseline or parsed_groups != groups:
                QMessageBox.critical(self, self.tr("Error"), self.tr("The prepared PAM profile did not match the requested settings."))
                return
            if groups and not self._verify_group_routing(groups, updated):
                QMessageBox.critical(self, self.tr("Error"), self.tr("Group routing validation failed."))
                return

        command = self._create_command(self._original_text, updated, self._managed_path)
        if command is None:
            QMessageBox.critical(self, self.tr("Error"), self.tr("Failed to prepare safe changes."))
            return

        question = self.tr("Apply password policy changes? A backup of the configuration will be created.")
        if groups:
            question += "\n" + self.tr("For users in several groups, the first matching group in alphabetical order takes precedence.")
        result = QMessageBox.question(
            self, self.tr("Apply"), question,
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
            QMessageBox.StandardButton.No
        )
        if result != QMessageBox.StandardButton.Yes:
            return

        self.lbl_status.setText(self.tr("Applying settings..."))
        self.btn_apply.setEnabled(False)
        self.btn_reset.setEnabled(False)
        self.list_groups.setEnabled(False)

        self.proc_apply = QProcess(self)
        self.proc_apply.setProcessEnvironment(QProcessEnvironment.systemEnvironment())
        self.proc_apply.finished.connect(self._on_apply_finished)
        self.proc_apply.errorOccurred.connect(self._on_apply_error)
        self.proc_apply.start("pkexec", ["/bin/sh", "-c", command])

    def _verify_group_routing(self, groups, text):
        ordered = sorted(groups)
        lines = self._password_lines(text)
        if len(lines) != len(ordered) * 4 + 3:
            return False
        cases = [set(), set(ordered)]
        cases.extend({name} for name in ordered)
        for i, name in enumerate(ordered):
            for next_name in ordered[i + 1:]:
                cases.append({name, next_name})

        for membership in cases:
            index = 0
            count_quality = 0
            count_history = 0
            count_tcb = 0
            steps = 0
            while index < len(lines) and steps <= len(lines):
                steps += 1
                line = lines[index]
                if "pam_succeed_if.so" in line:
                    name = line.split()[-1]
                    if name not in groups:
                        return False
                    if "auth_err=3" in line:
                        index += 1 if name in membership else 4
                    else:
                        if name not in membership:
                            return False
                        match = re.search(r"\[success=(\d+) default=die\]", line)
                        if not match:
                            return False
                        index += int(match.group(1)) + 1
                elif "pam_pwquality.so" in line:
                    count_quality += 1
                    index += 1
                elif "pam_pwhistory.so" in line:
                    count_history += 1
                    index += 1
                elif "pam_tcb.so" in line:
                    count_tcb += 1
                    index += 1
                else:
                    return False

            if (index != len(lines) or count_quality != 1 or
                    count_history != 1 or count_tcb != 1):
                return False
        return True

    def _on_apply_error(self, error):
        if self.proc_apply is not None and self.proc_apply.state() == QProcess.ProcessState.NotRunning:
            self.lbl_status.setText(self.tr("Failed to start the privileged process."))
            self.btn_reset.setEnabled(self._can_write)
            self.list_groups.setEnabled(True)
            self._update_apply_button()

    def _translate_apply_message(self, message):
        lines = []
        for line in message.splitlines():
            if line == "Active PAM chain changed externally":
                line = self.tr("Active PAM chain changed externally")
            elif line == "Configuration changed externally":
                line = self.tr("Configuration changed externally")
            elif line.startswith("Rollback failed. Backup: "):
                line = self.tr("Rollback failed. Backup: {backup}").format(
                    backup=line[len("Rollback failed. Backup: "):]
                )
            else:
                match = re.fullmatch(r"Backup: (.+) \(up to 5 dated copies per file in (.+)\)", line)
                if match:
                    line = self.tr("Backup: {backup} (up to 5 dated copies per file in {directory})").format(
                        backup=match.group(1), directory=match.group(2)
                    )
            lines.append(line)
        return "\n".join(lines)

    def _on_apply_finished(self, exit_code, exit_status):
        stderr = self.proc_apply.readAllStandardError().data().decode("utf-8", errors="replace").strip()
        stdout = self.proc_apply.readAllStandardOutput().data().decode("utf-8", errors="replace").strip()
        stderr = self._translate_apply_message(stderr)
        stdout = self._translate_apply_message(stdout)

        self.btn_reset.setEnabled(self._can_write)
        self.list_groups.setEnabled(True)

        if exit_code == 0:
            self._load(preserve_selection=True)
            self.lbl_status.setText(self.tr("Settings applied.") + (" " + stdout if stdout else ""))
            return

        self.lbl_status.setText(stderr or self.tr("Failed to apply settings. No changes were confirmed."))
        self._update_apply_button()

    def _on_reset(self):
        if not self._can_write:
            return
        defaults = self._default_state()
        if self._module_kind == "passwdqc":
            defaults["minlen"] = 13
        self._apply_state_to_form(defaults)
        for key in self._selected_groups():
            self._drafts[key] = dict(defaults)
        self._update_apply_button()


class PasswordPlugin(plugins.Base):
    requires_admin = True

    def __init__(self, plist=None, pane: QStackedWidget = None):
        super().__init__("password_policy", 170, plist, pane)

        if self.plist is not None and self.pane is not None:
            self.node = QStandardItem(self.tr("Password parameters"))
            self.node.setData(self.name)
            self.node.setData(self.name)
            self.add_to_menu(self.node)
            self.pane.addWidget(QWidget())

    def _do_start(self, idx: int):
        main_palette = self.pane.window().palette()
        self.pane.insertWidget(idx, PasswordWidget(main_palette))
