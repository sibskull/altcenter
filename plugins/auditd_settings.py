#!/usr/bin/python3

import plugins
import os
import json
from PyQt5.QtWidgets import QWidget, QVBoxLayout, QHBoxLayout, QStackedWidget, QListWidget, QListWidgetItem, QTextEdit, QSplitter, QLabel, QPushButton, QLineEdit, QComboBox, QCheckBox
from PyQt5.QtGui import QStandardItem, QStandardItemModel, QFont
from PyQt5.QtCore import Qt, QProcess, QProcessEnvironment, QLocale

class JournalsWidget(QWidget):
    def __init__(self, main_window = None):
        super().__init__()
        self.main_window = main_window

        self.proc_apply = None
        self.proc_load = None

        self.max_log_file_value = None
        self.num_logs_value = None
        self.space_left_value = None
        self.admin_space_left_value = None
        self.identity_audit_checkbox = None

        self.btn_apply = None
        self.lbl_status = None

        self.initUI()
        self.loadSavedLimits()
        self.loadSavedRules()

    def initUI(self):
        layout = QVBoxLayout()
        layout.setContentsMargins(10, 10, 10, 10)

        max_log_file = QHBoxLayout()

        max_log_file.addWidget(QLabel(self.tr("SystemMaxFileSize (MB):")))

        self.max_log_file_value = QLineEdit()
        self.max_log_file_value.setText("")
        max_log_file.addWidget(self.max_log_file_value, 1)

        max_log_file.addStretch(1)
        layout.addLayout(max_log_file)

        num_logs = QHBoxLayout()

        num_logs.addWidget(QLabel(self.tr("Max log files count:")))

        self.num_logs_value = QLineEdit()
        self.num_logs_value.setText("")
        num_logs.addWidget(self.num_logs_value, 1)

        num_logs.addStretch(1)
        layout.addLayout(num_logs)

        space_left = QHBoxLayout()

        space_left.addWidget(QLabel(self.tr("SystemKeepFree (MB):")))

        self.space_left_value = QLineEdit()
        self.space_left_value.setText("")
        space_left.addWidget(self.space_left_value, 1)

        space_left.addStretch(1)
        layout.addLayout(space_left)

        admin_space_left = QHBoxLayout()

        admin_space_left.addWidget(QLabel(self.tr("AdminSpaceLeft (MB):")))

        self.admin_space_left_value = QLineEdit()
        self.admin_space_left_value.setText("")
        admin_space_left.addWidget(self.admin_space_left_value, 1)

        admin_space_left.addStretch(1)
        layout.addLayout(admin_space_left)

        identity_audit = QHBoxLayout()

        self.identity_audit_checkbox = QCheckBox(self.tr("Audit password and account changes"))
        identity_audit.addWidget(self.identity_audit_checkbox)

        identity_audit.addStretch(1)
        layout.addLayout(identity_audit)

        apply_layout = QHBoxLayout()

        self.btn_apply = QPushButton(self.tr("Apply"))
        self.btn_apply.clicked.connect(self.on_apply_clicked)
        apply_layout.addWidget(self.btn_apply)

        self.lbl_status = QLabel("")
        self.lbl_status.setTextInteractionFlags(Qt.TextSelectableByMouse)
        apply_layout.addWidget(self.lbl_status)

        apply_layout.addStretch(1)
        layout.addLayout(apply_layout)

        layout.addStretch(1)
        self.setLayout(layout)

    def buildAuditdConfig(self, max_log_file, num_logs, space_left, admin_space_left):
        path = "/etc/audit/auditd.conf"
        try:
            with open(path, "r", encoding="utf-8", errors="replace") as f:
                lines = f.read().splitlines()
        except:
            lines = []

        values = [
            ("max_log_file", str(max_log_file)),
            ("max_log_file_action", "rotate"),
            ("num_logs", str(num_logs)),
            ("space_left", str(space_left)),
            ("admin_space_left", str(admin_space_left)),
        ]

        out = []
        seen = set()

        for raw in lines:
            line = raw.strip()
            replaced = False

            for key, value in values:
                if line.startswith(key + "=") or line.startswith(key + " ="):
                    out.append(f"{key} = {value}")
                    seen.add(key)
                    replaced = True
                    break

            if not replaced:
                out.append(raw)

        for key, value in values:
            if key not in seen:
                out.append(f"{key} = {value}")

        return "\n".join(out).rstrip("\n") + "\n"
    
    def loadSavedLimits(self):
        path = "/tmp/altcenter_auditd.conf"
        try:
            with open(path, "r", encoding="utf-8", errors="replace") as f:
                lines = f.read().splitlines()
        except:
            return

        self.max_log_file_value.setText("")
        self.num_logs_value.setText("")
        self.space_left_value.setText("")
        self.admin_space_left_value.setText("")

        mapping = [
            ("max_log_file", self.max_log_file_value),
            ("num_logs", self.num_logs_value),
            ("space_left", self.space_left_value),
            ("admin_space_left", self.admin_space_left_value),
        ]

        for raw in lines:
            line = raw.strip()
            if not line or line.startswith("#"):
                continue

            for key, widget in mapping:
                prefix1 = key + "="
                prefix2 = key + " ="
                if line.startswith(prefix1):
                    v = line[len(prefix1):].strip()
                elif line.startswith(prefix2):
                    v = line[len(prefix2):].strip()
                else:
                    continue

                if v.isdigit():
                    widget.setText(v)

    def hasRuleForPath(self, lines, path):
        for raw in lines:
            line = raw.strip()
            if not line or line.startswith("#"):
                continue

            if ("-w " + path) in line:
                return True

            if ("path=" + path) in line:
                return True

        return False

    def loadSavedRules(self):
        path = "/tmp/altcenter_audit.rules"
        try:
            with open(path, "r", encoding="utf-8", errors="replace") as f:
                lines = f.read().splitlines()
        except:
            self.identity_audit_checkbox.setChecked(False)
            return

        passwd_rule = self.hasRuleForPath(lines, "/etc/passwd")
        shadow_rule = self.hasRuleForPath(lines, "/etc/shadow")
        group_rule = self.hasRuleForPath(lines, "/etc/group")
        gshadow_rule = self.hasRuleForPath(lines, "/etc/gshadow")

        self.identity_audit_checkbox.setChecked(passwd_rule and shadow_rule and group_rule and gshadow_rule)

    def on_apply_clicked(self):
        if self.proc_apply != None and self.proc_apply.state() != QProcess.NotRunning:
            return

        t = self.max_log_file_value.text().strip()
        try:
            max_log_file = int(t)
        except:
            self.lbl_status.setText(self.tr("Enter a numeric value"))
            return

        if max_log_file <= 0:
            self.lbl_status.setText(self.tr("Enter a numeric value"))
            return

        t = self.num_logs_value.text().strip()
        try:
            num_logs = int(t)
        except:
            self.lbl_status.setText(self.tr("Enter a numeric value"))
            return

        if num_logs <= 1 or num_logs > 999:
            self.lbl_status.setText(self.tr("Enter a value from 2 to 999 to 'Max log files'"))
            return

        t = self.space_left_value.text().strip()
        try:
            space_left = int(t)
        except:
            self.lbl_status.setText(self.tr("Enter a numeric value"))
            return

        if space_left <= 0:
            self.lbl_status.setText(self.tr("Enter a numeric value"))
            return

        t = self.admin_space_left_value.text().strip()
        try:
            admin_space_left = int(t)
        except:
            self.lbl_status.setText(self.tr("Enter a numeric value"))
            return

        if admin_space_left <= 0:
            self.lbl_status.setText(self.tr("Enter a numeric value"))
            return

        if admin_space_left >= space_left:
            self.lbl_status.setText(self.tr("Critical free space must be lower than minimum free space"))
            return

        identity_rules = ""
        if self.identity_audit_checkbox.isChecked():
            identity_rules = (
                "# ALT Center: identity begin\n"
                "-w /etc/passwd -p wa -k identity\n"
                "-w /etc/shadow -p wa -k identity\n"
                "-w /etc/group -p wa -k identity\n"
                "-w /etc/gshadow -p wa -k identity\n"
                "# ALT Center: identity end\n"
            )

        identity_rules = identity_rules.replace("'", "'\"'\"'")

        self.lbl_status.setText("")
        self.btn_apply.setEnabled(False)

        if self.identity_audit_checkbox.isChecked():
            rules_cmd = (
                "mkdir -p /etc/audit/rules.d && "
                f"printf '%s' '{identity_rules}' > /etc/audit/rules.d/70-altcenter.rules && "
                "chmod 600 /etc/audit/rules.d/70-altcenter.rules"
            )
        else:
            rules_cmd = (
                "mkdir -p /etc/audit/rules.d && "
                ": > /etc/audit/rules.d/70-altcenter.rules && "
                "chmod 600 /etc/audit/rules.d/70-altcenter.rules"
            )

        cmd = (
            "grep -qiE '^\\s*max_log_file\\s*=' /etc/audit/auditd.conf "
            f"&& sed -i 's|^\\s*max_log_file\\s*=.*|max_log_file = {max_log_file}|I' /etc/audit/auditd.conf "
            f"|| printf '\\nmax_log_file = {max_log_file}\\n' >> /etc/audit/auditd.conf; "

            "grep -qiE '^\\s*max_log_file_action\\s*=' /etc/audit/auditd.conf "
            "&& sed -i 's|^\\s*max_log_file_action\\s*=.*|max_log_file_action = ROTATE|I' /etc/audit/auditd.conf "
            "|| printf 'max_log_file_action = ROTATE\\n' >> /etc/audit/auditd.conf; "

            "grep -qiE '^\\s*num_logs\\s*=' /etc/audit/auditd.conf "
            f"&& sed -i 's|^\\s*num_logs\\s*=.*|num_logs = {num_logs}|I' /etc/audit/auditd.conf "
            f"|| printf 'num_logs = {num_logs}\\n' >> /etc/audit/auditd.conf; "

            "grep -qiE '^\\s*space_left\\s*=' /etc/audit/auditd.conf "
            f"&& sed -i 's|^\\s*space_left\\s*=.*|space_left = {space_left}|I' /etc/audit/auditd.conf "
            f"|| printf 'space_left = {space_left}\\n' >> /etc/audit/auditd.conf; "

            "grep -qiE '^\\s*admin_space_left\\s*=' /etc/audit/auditd.conf "
            f"&& sed -i 's|^\\s*admin_space_left\\s*=.*|admin_space_left = {admin_space_left}|I' /etc/audit/auditd.conf "
            f"|| printf 'admin_space_left = {admin_space_left}\\n' >> /etc/audit/auditd.conf; "

            "cat /etc/audit/auditd.conf > /tmp/altcenter_auditd.conf && chmod 644 /tmp/altcenter_auditd.conf && "
            + rules_cmd + " && "
            + "cat /etc/audit/rules.d/*.rules > /tmp/altcenter_audit.rules 2>/dev/null || : && "
            + "chmod 644 /tmp/altcenter_audit.rules 2>/dev/null || : && "
            + "if command -v augenrules >/dev/null 2>&1; then augenrules --load; fi && "
            + "if command -v service >/dev/null 2>&1; then service auditd restart; else systemctl restart auditd; fi"
        )

        self.proc_apply = QProcess(self)
        env = QProcessEnvironment.systemEnvironment()
        self.proc_apply.setProcessEnvironment(env)
        self.proc_apply.finished.connect(self.on_apply_finished)
        self.proc_apply.start("pkexec", ["sh", "-c", cmd])

    def on_apply_finished(self, exit_code, exit_status):
        err = self.proc_apply.readAllStandardError().data().decode(errors="replace").strip()

        self.btn_apply.setEnabled(True)

        if exit_code == 0:
            self.lbl_status.setText(self.tr("Done"))
            self.loadSavedLimits()
            self.loadSavedRules()
            return

        if err:
            self.lbl_status.setText(err)
        else:
            self.lbl_status.setText(self.tr("Failed"))


class PluginJournals(plugins.Base):
    requires_admin = True
    def __init__(self, plist: QStandardItemModel=None, pane: QStackedWidget = None):
        super().__init__("auditd_settings", 120, plist, pane)

        if self.plist != None and self.pane != None:
            self.node = QStandardItem(self.tr("Auditd logs settings"))
            self.node.setData(self.name)
            self.plist.appendRow([self.node])
            self.pane.addWidget(QWidget())

    def _do_start(self, idx: int):
        main_window = self.pane.window()
        main_widget = JournalsWidget(main_window)
        self.pane.insertWidget(idx, main_widget)