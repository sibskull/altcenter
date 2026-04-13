#!/usr/bin/python3

import plugins
import os
import json
from PyQt5.QtWidgets import QWidget, QVBoxLayout, QHBoxLayout, QStackedWidget, QListWidget, QListWidgetItem, QTextEdit, QSplitter, QLabel, QPushButton, QLineEdit, QComboBox, QCheckBox, QScrollArea
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
        self.audit_config_audit_checkbox = None
        self.audit_log_read_checkbox = None
        self.journald_config_audit_checkbox = None
        self.password_policy_audit_checkbox = None
        self.privileged_commands_audit_checkbox = None
        self.network_config_audit_checkbox = None
        self.kernel_module_audit_checkbox = None
        self.account_modification_audit_checkbox = None
        self.file_delete_audit_checkbox = None
        self.mount_export_audit_checkbox = None
        self.discretionary_access_audit_checkbox = None
        self.unauthorized_access_audit_checkbox = None

        self.btn_apply = None
        self.lbl_status = None

        self.initUI()
        self.loadSavedLimits()
        self.loadSavedRules()

    def initUI(self):
        root_layout = QVBoxLayout(self)
        root_layout.setContentsMargins(0, 0, 0, 0)

        scroll = QScrollArea()
        scroll.setWidgetResizable(True)

        container = QWidget()
        layout = QVBoxLayout(container)
        layout.setContentsMargins(10, 10, 10, 10)

        max_log_file = QHBoxLayout()

        max_log_file.addWidget(QLabel(self.tr("SystemMaxFileSize (MB):")))

        self.max_log_file_value = QLineEdit()
        self.max_log_file_value.setText("")
        max_log_file.addWidget(self.max_log_file_value, 1)

        max_log_file.addStretch(1)
        layout.addLayout(max_log_file)

        num_logs = QHBoxLayout()

        num_logs.addWidget(QLabel(self.tr("Maximum number of log files:")))

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

        audit_config_audit = QHBoxLayout()

        self.audit_config_audit_checkbox = QCheckBox(self.tr("Audit audit configuration changes"))
        audit_config_audit.addWidget(self.audit_config_audit_checkbox)

        audit_config_audit.addStretch(1)
        layout.addLayout(audit_config_audit)

        audit_log_read = QHBoxLayout()

        self.audit_log_read_checkbox = QCheckBox(self.tr("Audit audit log read/export"))
        audit_log_read.addWidget(self.audit_log_read_checkbox)

        audit_log_read.addStretch(1)
        layout.addLayout(audit_log_read)

        journald_config_audit = QHBoxLayout()

        self.journald_config_audit_checkbox = QCheckBox(self.tr("Audit journald configuration changes"))
        journald_config_audit.addWidget(self.journald_config_audit_checkbox)

        journald_config_audit.addStretch(1)
        layout.addLayout(journald_config_audit)

        password_policy_audit = QHBoxLayout()

        self.password_policy_audit_checkbox = QCheckBox(self.tr("Audit password policy configuration changes"))
        password_policy_audit.addWidget(self.password_policy_audit_checkbox)

        password_policy_audit.addStretch(1)
        layout.addLayout(password_policy_audit)

        privileged_commands_audit = QHBoxLayout()

        self.privileged_commands_audit_checkbox = QCheckBox(self.tr("Audit privileged commands usage"))
        privileged_commands_audit.addWidget(self.privileged_commands_audit_checkbox)

        privileged_commands_audit.addStretch(1)
        layout.addLayout(privileged_commands_audit)

        network_config_audit = QHBoxLayout()

        self.network_config_audit_checkbox = QCheckBox(self.tr("Audit network environment changes"))
        network_config_audit.addWidget(self.network_config_audit_checkbox)

        network_config_audit.addStretch(1)
        layout.addLayout(network_config_audit)

        kernel_module_audit = QHBoxLayout()

        self.kernel_module_audit_checkbox = QCheckBox(self.tr("Audit kernel module changes"))
        kernel_module_audit.addWidget(self.kernel_module_audit_checkbox)

        kernel_module_audit.addStretch(1)
        layout.addLayout(kernel_module_audit)

        account_modification_audit = QHBoxLayout()

        self.account_modification_audit_checkbox = QCheckBox(self.tr("Audit account modification commands"))
        account_modification_audit.addWidget(self.account_modification_audit_checkbox)

        account_modification_audit.addStretch(1)
        layout.addLayout(account_modification_audit)

        file_delete_audit = QHBoxLayout()

        self.file_delete_audit_checkbox = QCheckBox(self.tr("Audit file deletion events"))
        file_delete_audit.addWidget(self.file_delete_audit_checkbox)

        file_delete_audit.addStretch(1)
        layout.addLayout(file_delete_audit)

        mount_export_audit = QHBoxLayout()

        self.mount_export_audit_checkbox = QCheckBox(self.tr("Audit information export to media"))
        mount_export_audit.addWidget(self.mount_export_audit_checkbox)

        mount_export_audit.addStretch(1)
        layout.addLayout(mount_export_audit)

        discretionary_access_audit = QHBoxLayout()

        self.discretionary_access_audit_checkbox = QCheckBox(self.tr("Audit discretionary access changes"))
        discretionary_access_audit.addWidget(self.discretionary_access_audit_checkbox)

        discretionary_access_audit.addStretch(1)
        layout.addLayout(discretionary_access_audit)

        unauthorized_access_audit = QHBoxLayout()

        self.unauthorized_access_audit_checkbox = QCheckBox(self.tr("Audit unauthorized access attempts"))
        unauthorized_access_audit.addWidget(self.unauthorized_access_audit_checkbox)

        unauthorized_access_audit.addStretch(1)
        layout.addLayout(unauthorized_access_audit)

        apply_layout = QHBoxLayout()

        self.btn_apply = QPushButton(self.tr("Apply"))
        self.btn_apply.setMinimumHeight(32)
        self.btn_apply.clicked.connect(self.on_apply_clicked)
        apply_layout.addWidget(self.btn_apply)

        self.lbl_status = QLabel("")
        self.lbl_status.setTextInteractionFlags(Qt.TextSelectableByMouse)
        apply_layout.addWidget(self.lbl_status)

        apply_layout.addStretch(1)
        layout.addLayout(apply_layout)

        layout.addStretch(1)

        scroll.setWidget(container)
        root_layout.addWidget(scroll)

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

            if line.startswith("-w "):
                parts = line.split()
                if len(parts) >= 2 and parts[1] == path:
                    return True

            if ("path=" + path) in line:
                return True

        return False

    def hasAllExistingPaths(self, lines, paths):
        has_existing = False

        for path in paths:
            if not os.path.exists(path):
                continue

            has_existing = True

            if not self.hasRuleForPath(lines, path):
                return False

        return has_existing

    def hasAllConfiguredPaths(self, lines, paths):
        for path in paths:
            if not self.hasRuleForPath(lines, path):
                return False

        return True

    def hasRuleForSyscall(self, lines, syscall_name, key):
        for raw in lines:
            line = raw.strip()
            if not line or line.startswith("#"):
                continue

            if ("-S " + syscall_name) in line and (("-k " + key) in line or ("key=" + key) in line):
                return True

        return False

    def hasDeniedRuleForSyscall(self, lines, syscall_name, key):
        for raw in lines:
            line = raw.strip()
            if not line or line.startswith("#"):
                continue

            if ("-S " + syscall_name) not in line:
                continue

            if ("-k " + key) not in line and ("key=" + key) not in line:
                continue

            if "exit=-EACCES" in line or "exit=-EPERM" in line:
                return True

        return False

    def buildWatchRules(self, block_name, key, rules, include_missing = False):
        parts = ["# ALT Center: %s begin" % block_name]
        has_rules = False

        for path, perm in rules:
            if not include_missing and not os.path.exists(path):
                continue

            parts.append("-w %s -p %s -k %s" % (path, perm, key))
            has_rules = True

        parts.append("# ALT Center: %s end" % block_name)

        if not has_rules:
            return ""

        return "\n".join(parts) + "\n"

    def getAuditArchitectures(self):
        machine = os.uname().machine.lower()

        if machine in ("x86_64", "amd64"):
            return ["b64", "b32"]

        if machine in ("i386", "i486", "i586", "i686"):
            return ["b32"]

        return ["b64"]

    def buildSyscallRules(self, block_name, key, syscalls):
        parts = ["# ALT Center: %s begin" % block_name]

        for arch in self.getAuditArchitectures():
            line = "-a always,exit -F arch=%s" % arch

            for syscall_name in syscalls:
                line += " -S %s" % syscall_name

            line += " -k %s" % key
            parts.append(line)

        parts.append("# ALT Center: %s end" % block_name)
        return "\n".join(parts) + "\n"

    def buildDeniedAccessRules(self, block_name, key, syscalls):
        parts = ["# ALT Center: %s begin" % block_name]

        for arch in self.getAuditArchitectures():
            line_eacces = "-a always,exit -F arch=%s" % arch
            line_eperm = "-a always,exit -F arch=%s" % arch

            for syscall_name in syscalls:
                line_eacces += " -S %s" % syscall_name
                line_eperm += " -S %s" % syscall_name

            line_eacces += " -F exit=-EACCES -k %s" % key
            line_eperm += " -F exit=-EPERM -k %s" % key

            parts.append(line_eacces)
            parts.append(line_eperm)

        parts.append("# ALT Center: %s end" % block_name)
        return "\n".join(parts) + "\n"

    def loadSavedRules(self):
        path = "/tmp/altcenter_audit.rules"

        try:
            with open(path, "r", encoding="utf-8", errors="replace") as f:
                lines = f.read().splitlines()
        except:
            self.identity_audit_checkbox.setChecked(False)
            self.audit_config_audit_checkbox.setChecked(False)
            self.audit_log_read_checkbox.setChecked(False)
            self.journald_config_audit_checkbox.setChecked(False)
            self.password_policy_audit_checkbox.setChecked(False)
            self.privileged_commands_audit_checkbox.setChecked(False)
            self.network_config_audit_checkbox.setChecked(False)
            self.kernel_module_audit_checkbox.setChecked(False)
            self.account_modification_audit_checkbox.setChecked(False)
            self.file_delete_audit_checkbox.setChecked(False)
            self.mount_export_audit_checkbox.setChecked(False)
            self.discretionary_access_audit_checkbox.setChecked(False)
            self.unauthorized_access_audit_checkbox.setChecked(False)
            return

        passwd_rule = self.hasRuleForPath(lines, "/etc/passwd")
        shadow_rule = self.hasRuleForPath(lines, "/etc/shadow")
        group_rule = self.hasRuleForPath(lines, "/etc/group")
        gshadow_rule = self.hasRuleForPath(lines, "/etc/gshadow")

        passwd_exec_rule = True
        passwd_exec_exists = False

        for path in ["/usr/bin/passwd", "/bin/passwd"]:
            if not os.path.exists(path):
                continue

            passwd_exec_exists = True

            if self.hasRuleForPath(lines, path):
                passwd_exec_rule = True
                break

            passwd_exec_rule = False

        if not passwd_exec_exists:
            passwd_exec_rule = True

        audit_config_rule = self.hasRuleForPath(lines, "/etc/audit")
        audit_log_rule = self.hasRuleForPath(lines, "/var/log/audit")

        journald_config_rule = self.hasAllConfiguredPaths(lines, [
            "/etc/systemd/journald.conf",
            "/etc/systemd/journald.conf.d",
        ])

        password_policy_rule = self.hasAllExistingPaths(lines, [
            "/etc/passwdqc.conf",
            "/etc/pam.d/system-auth-local-only",
        ])

        privileged_commands_rule = self.hasAllExistingPaths(lines, [
            "/etc/sudoers",
            "/etc/sudoers.d",
            "/bin/su",
            "/usr/bin/sudo",
        ])

        network_config_rule = self.hasAllExistingPaths(lines, [
            "/etc/net/ifaces",
            "/etc/sysconfig/network",
            "/etc/hosts",
            "/etc/hostname",
            "/etc/net",
            "/etc/netconfig",
            "/etc/NetworkManager",
            "/usr/bin/hostnamectl",
        ])

        kernel_module_rule = (
            (
                self.hasRuleForPath(lines, "/usr/bin/kmod")
                or self.hasRuleForPath(lines, "/sbin/modprobe")
                or self.hasRuleForPath(lines, "/usr/sbin/modprobe")
                or self.hasRuleForPath(lines, "/sbin/insmod")
                or self.hasRuleForPath(lines, "/sbin/rmmod")
            )
            and self.hasRuleForPath(lines, "/etc/sysctl.conf")
        )

        account_modification_rule = self.hasAllExistingPaths(lines, [
            "/usr/sbin/adduser",
            "/usr/sbin/useradd",
            "/usr/sbin/usermod",
            "/usr/bin/gpasswd",
        ])

        file_delete_syscalls = [
            "rmdir",
            "unlinkat",
            "rename",
            "renameat",
            "unlink",
        ]

        file_delete_rule = True
        for syscall_name in file_delete_syscalls:
            if not self.hasRuleForSyscall(lines, syscall_name, "file_delete"):
                file_delete_rule = False
                break

        mount_export_rule = self.hasRuleForSyscall(lines, "mount", "mount_export")

        discretionary_access_syscalls = [
            "chown",
            "fchown",
            "fchownat",
            "lchown",
            "removexattr",
            "lremovexattr",
            "fremovexattr",
            "setxattr",
            "fsetxattr",
            "lsetxattr",
            "chmod",
            "fchmod",
            "fchmodat",
        ]

        discretionary_access_rule = True
        for syscall_name in discretionary_access_syscalls:
            if not self.hasRuleForSyscall(lines, syscall_name, "discretionary_access"):
                discretionary_access_rule = False
                break

        unauthorized_access_syscalls = [
            "truncate",
            "creat",
            "ftruncate",
            "open",
            "openat",
            "open_by_handle_at",
        ]

        unauthorized_access_rule = True
        for syscall_name in unauthorized_access_syscalls:
            if not self.hasDeniedRuleForSyscall(lines, syscall_name, "unauthorized_access"):
                unauthorized_access_rule = False
                break

        self.identity_audit_checkbox.setChecked(
            passwd_rule and shadow_rule and group_rule and gshadow_rule and passwd_exec_rule
        )
        self.audit_config_audit_checkbox.setChecked(audit_config_rule)
        self.audit_log_read_checkbox.setChecked(audit_log_rule)
        self.journald_config_audit_checkbox.setChecked(journald_config_rule)
        self.password_policy_audit_checkbox.setChecked(password_policy_rule)
        self.privileged_commands_audit_checkbox.setChecked(privileged_commands_rule)
        self.network_config_audit_checkbox.setChecked(network_config_rule)
        self.kernel_module_audit_checkbox.setChecked(kernel_module_rule)
        self.account_modification_audit_checkbox.setChecked(account_modification_rule)
        self.file_delete_audit_checkbox.setChecked(file_delete_rule)
        self.mount_export_audit_checkbox.setChecked(mount_export_rule)
        self.discretionary_access_audit_checkbox.setChecked(discretionary_access_rule)
        self.unauthorized_access_audit_checkbox.setChecked(unauthorized_access_rule)

    def loadSavedNumericValues(self):
        path = "/tmp/altcenter_auditd.conf"
        values = {}

        try:
            with open(path, "r", encoding="utf-8", errors="replace") as f:
                lines = f.read().splitlines()
        except:
            return values

        for raw in lines:
            line = raw.strip()
            if not line or line.startswith("#") or "=" not in line:
                continue

            key, value = line.split("=", 1)
            key = key.strip()
            value = value.strip()

            if value.isdigit():
                values[key] = int(value)

        return values

    def parseOptionalInteger(self, text):
        t = text.strip()

        if not t:
            return True, None

        try:
            v = int(t)
        except:
            return False, None

        return True, v

    def on_apply_clicked(self):
        if self.proc_apply != None and self.proc_apply.state() != QProcess.NotRunning:
            return

        ok, max_log_file = self.parseOptionalInteger(self.max_log_file_value.text())
        if not ok:
            self.lbl_status.setText(self.tr("Enter a numeric value"))
            return

        if max_log_file != None and max_log_file <= 0:
            self.lbl_status.setText(self.tr("Enter a numeric value"))
            return

        ok, num_logs = self.parseOptionalInteger(self.num_logs_value.text())
        if not ok:
            self.lbl_status.setText(self.tr("Enter a numeric value"))
            return

        if num_logs != None and (num_logs <= 1 or num_logs > 999):
            self.lbl_status.setText(self.tr("Enter a value from 2 to 999 to 'Maximum number of log files'"))
            return

        ok, space_left = self.parseOptionalInteger(self.space_left_value.text())
        if not ok:
            self.lbl_status.setText(self.tr("Enter a numeric value"))
            return

        if space_left != None and space_left <= 0:
            self.lbl_status.setText(self.tr("Enter a numeric value"))
            return

        ok, admin_space_left = self.parseOptionalInteger(self.admin_space_left_value.text())
        if not ok:
            self.lbl_status.setText(self.tr("Enter a numeric value"))
            return

        if admin_space_left != None and admin_space_left <= 0:
            self.lbl_status.setText(self.tr("Enter a numeric value"))
            return

        saved_values = self.loadSavedNumericValues()

        effective_space_left = space_left
        if effective_space_left == None:
            effective_space_left = saved_values.get("space_left")

        effective_admin_space_left = admin_space_left
        if effective_admin_space_left == None:
            effective_admin_space_left = saved_values.get("admin_space_left")

        if effective_space_left != None and effective_admin_space_left != None:
            if effective_admin_space_left >= effective_space_left:
                self.lbl_status.setText(self.tr("Critical free space must be lower than minimum free space"))
                return

        identity_rules = ""
        if self.identity_audit_checkbox.isChecked():
            identity_rules = self.buildWatchRules(
                "identity",
                "identity",
                [
                    ("/etc/passwd", "wa"),
                    ("/etc/shadow", "wa"),
                    ("/etc/group", "wa"),
                    ("/etc/gshadow", "wa"),
                    ("/usr/bin/passwd", "x"),
                    ("/bin/passwd", "x"),
                ]
            )

        audit_config_rules = ""
        if self.audit_config_audit_checkbox.isChecked():
            audit_config_rules = (
                "# ALT Center: audit_config begin\n"
                "-w /etc/audit -p wa -k audit_config\n"
                "# ALT Center: audit_config end\n"
            )

        audit_log_rules = ""
        if self.audit_log_read_checkbox.isChecked():
            audit_log_rules = (
                "# ALT Center: audit_log begin\n"
                "-w /var/log/audit -p r -k audit_log\n"
                "# ALT Center: audit_log end\n"
            )

        journald_config_rules = ""
        if self.journald_config_audit_checkbox.isChecked():
            journald_config_rules = self.buildWatchRules(
                "journald_config",
                "journald_config",
                [
                    ("/etc/systemd/journald.conf", "wa"),
                    ("/etc/systemd/journald.conf.d", "wa"),
                ],
                include_missing = True
            )

        password_policy_rules = ""
        if self.password_policy_audit_checkbox.isChecked():
            password_policy_rules = self.buildWatchRules(
                "password_policy",
                "password_policy",
                [
                    ("/etc/passwdqc.conf", "wa"),
                    ("/etc/pam.d/system-auth-local-only", "wa"),
                ]
            )

        privileged_commands_rules = ""
        if self.privileged_commands_audit_checkbox.isChecked():
            privileged_commands_rules = self.buildWatchRules(
                "privileged_commands",
                "privileged_commands",
                [
                    ("/etc/sudoers", "wa"),
                    ("/etc/sudoers.d", "wa"),
                    ("/bin/su", "x"),
                    ("/usr/bin/sudo", "x"),
                ]
            )

        network_config_rules = ""
        if self.network_config_audit_checkbox.isChecked():
            network_config_rules = self.buildWatchRules(
                "network_config",
                "network_config",
                [
                    ("/etc/net/ifaces", "wa"),
                    ("/etc/sysconfig/network", "wa"),
                    ("/etc/hosts", "wa"),
                    ("/etc/hostname", "wa"),
                    ("/etc/net", "wa"),
                    ("/etc/netconfig", "wa"),
                    ("/etc/NetworkManager", "wa"),
                    ("/usr/bin/hostnamectl", "x"),
                ]
            )

        kernel_module_rules = ""
        if self.kernel_module_audit_checkbox.isChecked():
            kernel_module_rules = self.buildWatchRules(
                "kernel_module",
                "kernel_module",
                [
                    ("/usr/bin/kmod", "x"),
                    ("/sbin/insmod", "x"),
                    ("/sbin/rmmod", "x"),
                    ("/etc/sysctl.conf", "wa"),
                ]
            )

        account_modification_rules = ""
        if self.account_modification_audit_checkbox.isChecked():
            account_modification_rules = self.buildWatchRules(
                "account_modification",
                "account_modification",
                [
                    ("/usr/sbin/adduser", "x"),
                    ("/usr/sbin/useradd", "x"),
                    ("/usr/sbin/usermod", "x"),
                    ("/usr/bin/gpasswd", "x"),
                ]
            )

        file_delete_rules = ""
        if self.file_delete_audit_checkbox.isChecked():
            file_delete_rules = self.buildSyscallRules(
                "file_delete",
                "file_delete",
                [
                    "rmdir",
                    "unlinkat",
                    "rename",
                    "renameat",
                    "unlink",
                ]
            )

        mount_export_rules = ""
        if self.mount_export_audit_checkbox.isChecked():
            mount_export_rules = self.buildSyscallRules(
                "mount_export",
                "mount_export",
                [
                    "mount",
                ]
            )

        discretionary_access_rules = ""
        if self.discretionary_access_audit_checkbox.isChecked():
            discretionary_access_rules = self.buildSyscallRules(
                "discretionary_access",
                "discretionary_access",
                [
                    "chown",
                    "fchown",
                    "fchownat",
                    "lchown",
                    "removexattr",
                    "lremovexattr",
                    "fremovexattr",
                    "setxattr",
                    "fsetxattr",
                    "lsetxattr",
                    "chmod",
                    "fchmod",
                    "fchmodat",
                ]
            )

        unauthorized_access_rules = ""
        if self.unauthorized_access_audit_checkbox.isChecked():
            unauthorized_access_rules = self.buildDeniedAccessRules(
                "unauthorized_access",
                "unauthorized_access",
                [
                    "truncate",
                    "creat",
                    "ftruncate",
                    "open",
                    "openat",
                    "open_by_handle_at",
                ]
            )

        managed_rules = (
            identity_rules
            + audit_config_rules
            + audit_log_rules
            + journald_config_rules
            + password_policy_rules
            + privileged_commands_rules
            + network_config_rules
            + kernel_module_rules
            + account_modification_rules
            + file_delete_rules
            + mount_export_rules
            + discretionary_access_rules
            + unauthorized_access_rules
        )
        managed_rules = managed_rules.replace("'", "'\"'\"'")

        self.lbl_status.setText("")
        self.btn_apply.setEnabled(False)

        if managed_rules:
            rules_cmd = (
                "mkdir -p /etc/audit/rules.d && "
                f"printf '%s' '{managed_rules}' > /etc/audit/rules.d/70-altcenter.rules && "
                "chmod 600 /etc/audit/rules.d/70-altcenter.rules"
            )
        else:
            rules_cmd = (
                "mkdir -p /etc/audit/rules.d && "
                ": > /etc/audit/rules.d/70-altcenter.rules && "
                "chmod 600 /etc/audit/rules.d/70-altcenter.rules"
            )

        config_cmd = ""

        if max_log_file != None:
            config_cmd += (
                "grep -qiE '^\\s*max_log_file\\s*=' /etc/audit/auditd.conf "
                f"&& sed -i 's|^\\s*max_log_file\\s*=.*|max_log_file = {max_log_file}|I' /etc/audit/auditd.conf "
                f"|| printf '\\nmax_log_file = {max_log_file}\\n' >> /etc/audit/auditd.conf; "
            )

        if max_log_file != None or num_logs != None:
            config_cmd += (
                "grep -qiE '^\\s*max_log_file_action\\s*=' /etc/audit/auditd.conf "
                "&& sed -i 's|^\\s*max_log_file_action\\s*=.*|max_log_file_action = ROTATE|I' /etc/audit/auditd.conf "
                "|| printf 'max_log_file_action = ROTATE\\n' >> /etc/audit/auditd.conf; "
            )

        if num_logs != None:
            config_cmd += (
                "grep -qiE '^\\s*num_logs\\s*=' /etc/audit/auditd.conf "
                f"&& sed -i 's|^\\s*num_logs\\s*=.*|num_logs = {num_logs}|I' /etc/audit/auditd.conf "
                f"|| printf 'num_logs = {num_logs}\\n' >> /etc/audit/auditd.conf; "
            )

        if space_left != None:
            config_cmd += (
                "grep -qiE '^\\s*space_left\\s*=' /etc/audit/auditd.conf "
                f"&& sed -i 's|^\\s*space_left\\s*=.*|space_left = {space_left}|I' /etc/audit/auditd.conf "
                f"|| printf 'space_left = {space_left}\\n' >> /etc/audit/auditd.conf; "
            )

        if admin_space_left != None:
            config_cmd += (
                "grep -qiE '^\\s*admin_space_left\\s*=' /etc/audit/auditd.conf "
                f"&& sed -i 's|^\\s*admin_space_left\\s*=.*|admin_space_left = {admin_space_left}|I' /etc/audit/auditd.conf "
                f"|| printf 'admin_space_left = {admin_space_left}\\n' >> /etc/audit/auditd.conf; "
            )

        cmd = (
            config_cmd
            + "cat /etc/audit/auditd.conf > /tmp/altcenter_auditd.conf && chmod 644 /tmp/altcenter_auditd.conf && "
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