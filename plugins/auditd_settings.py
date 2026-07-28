#!/usr/bin/python3

import plugins
import os
import json
import base64
from PyQt6.QtWidgets import QWidget, QVBoxLayout, QHBoxLayout, QStackedWidget, QListWidget, QListWidgetItem, QTextEdit, QSplitter, QLabel, QPushButton, QLineEdit, QComboBox, QCheckBox, QScrollArea, QFrame, QPlainTextEdit, QMessageBox
from PyQt6.QtGui import QStandardItem, QStandardItemModel, QFont
from PyQt6.QtCore import Qt, QProcess, QProcessEnvironment, QLocale, QEvent

class JournalsWidget(QWidget):
    def __init__(self, main_window = None):
        super().__init__()
        self.main_window = main_window

        self.proc_apply = None
        self.proc_load = None
        self.proc_save_custom = None

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
        self.system_power_audit_checkbox = None
        self.account_modification_audit_checkbox = None
        self.file_delete_audit_checkbox = None
        self.mount_export_audit_checkbox = None
        self.discretionary_access_audit_checkbox = None
        self.unauthorized_access_audit_checkbox = None

        self.btn_apply = None
        self.lbl_status = None

        self.custom_rules = []
        self.custom_rules_title = None
        self.custom_rules_widget = None
        self.custom_rules_layout = None
        self.custom_rule_name = None
        self.custom_rule_text = None
        self.btn_add_custom_rule = None
        self.lbl_custom_rule_status = None
        self.pending_custom_rule = None
        self.custom_rule_info_panel = None

        self.initial_form_state = None
        self.form_loading = False

        self.initUI()

        self.form_loading = True
        self.loadSavedLimits()
        self.loadSavedRules()
        self.loadSavedCustomRules()
        self.form_loading = False

        self.connectFormSignals()
        self.initial_form_state = self.getFormState()
        self.updateApplyButton()
        self.updateAddRuleButton()

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

        system_power_audit = QHBoxLayout()

        self.system_power_audit_checkbox = QCheckBox(self.tr("Audit system shutdown and reboot"))
        system_power_audit.addWidget(self.system_power_audit_checkbox)

        system_power_audit.addStretch(1)
        layout.addLayout(system_power_audit)

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

        self.custom_rules_title = QLabel(self.tr("User rules"))
        custom_rules_title_font = self.custom_rules_title.font()
        custom_rules_title_font.setBold(True)
        self.custom_rules_title.setFont(custom_rules_title_font)
        self.custom_rules_title.setVisible(False)
        layout.addWidget(self.custom_rules_title)

        self.custom_rules_widget = QWidget()
        self.custom_rules_layout = QVBoxLayout(self.custom_rules_widget)
        self.custom_rules_layout.setContentsMargins(0, 0, 0, 0)
        self.custom_rules_layout.setSpacing(6)
        self.custom_rules_widget.setVisible(False)
        layout.addWidget(self.custom_rules_widget)

        apply_layout = QHBoxLayout()

        self.btn_apply = QPushButton(self.tr("Apply"))
        self.btn_apply.setMinimumHeight(32)
        self.btn_apply.setEnabled(False)
        self.btn_apply.clicked.connect(self.on_apply_clicked)
        apply_layout.addWidget(self.btn_apply)

        self.lbl_status = QLabel("")
        self.lbl_status.setTextInteractionFlags(Qt.TextInteractionFlag.TextSelectableByMouse)
        apply_layout.addWidget(self.lbl_status)

        apply_layout.addStretch(1)
        layout.addLayout(apply_layout)

        separator = QFrame()
        separator.setFrameShape(QFrame.Shape.HLine)
        separator.setFrameShadow(QFrame.Shadow.Sunken)
        layout.addWidget(separator)

        custom_rule_title = QLabel(self.tr("Add user rule"))
        custom_rule_title_font = custom_rule_title.font()
        custom_rule_title_font.setBold(True)
        custom_rule_title.setFont(custom_rule_title_font)
        layout.addWidget(custom_rule_title)

        custom_rule_name_layout = QHBoxLayout()
        custom_rule_name_layout.addWidget(QLabel(self.tr("Rule name:")))

        self.custom_rule_name = QLineEdit()
        self.custom_rule_name.setMaxLength(120)
        self.custom_rule_name.textChanged.connect(self.updateAddRuleButton)
        custom_rule_name_layout.addWidget(self.custom_rule_name, 1)

        custom_rule_name_layout.addStretch(1)
        layout.addLayout(custom_rule_name_layout)

        layout.addWidget(QLabel(self.tr("Rule:")))

        self.custom_rule_text = QPlainTextEdit()
        self.custom_rule_text.setMinimumHeight(70)
        self.custom_rule_text.setMaximumHeight(100)
        self.custom_rule_text.setLineWrapMode(QPlainTextEdit.LineWrapMode.NoWrap)
        self.custom_rule_text.textChanged.connect(self.updateAddRuleButton)
        layout.addWidget(self.custom_rule_text)

        custom_rule_buttons_layout = QHBoxLayout()

        self.btn_add_custom_rule = QPushButton(self.tr("Save rule"))
        self.btn_add_custom_rule.setEnabled(False)
        self.btn_add_custom_rule.clicked.connect(self.onAddCustomRuleClicked)
        custom_rule_buttons_layout.addWidget(self.btn_add_custom_rule)

        self.lbl_custom_rule_status = QLabel("")
        self.lbl_custom_rule_status.setTextInteractionFlags(Qt.TextInteractionFlag.TextSelectableByMouse)
        self.lbl_custom_rule_status.setWordWrap(True)
        custom_rule_buttons_layout.addWidget(self.lbl_custom_rule_status, 1)

        custom_rule_buttons_layout.addStretch(1)
        layout.addLayout(custom_rule_buttons_layout)

        layout.addStretch(1)

        scroll.setWidget(container)

        splitter = QSplitter(Qt.Orientation.Horizontal)
        splitter.addWidget(scroll)

        self.custom_rule_info_panel = QTextEdit()
        self.custom_rule_info_panel.setReadOnly(True)
        self.custom_rule_info_panel.setMinimumWidth(200)
        self.custom_rule_info_panel.setVisible(False)
        splitter.addWidget(self.custom_rule_info_panel)

        splitter.setStretchFactor(0, 3)
        splitter.setStretchFactor(1, 2)

        root_layout.addWidget(splitter)

    def getRuleCheckboxes(self):
        return [
            self.identity_audit_checkbox,
            self.audit_config_audit_checkbox,
            self.audit_log_read_checkbox,
            self.journald_config_audit_checkbox,
            self.password_policy_audit_checkbox,
            self.privileged_commands_audit_checkbox,
            self.network_config_audit_checkbox,
            self.kernel_module_audit_checkbox,
            self.system_power_audit_checkbox,
            self.account_modification_audit_checkbox,
            self.file_delete_audit_checkbox,
            self.mount_export_audit_checkbox,
            self.discretionary_access_audit_checkbox,
            self.unauthorized_access_audit_checkbox,
        ]

    def connectFormSignals(self):
        self.max_log_file_value.textChanged.connect(self.onFormChanged)
        self.num_logs_value.textChanged.connect(self.onFormChanged)
        self.space_left_value.textChanged.connect(self.onFormChanged)
        self.admin_space_left_value.textChanged.connect(self.onFormChanged)

        for checkbox in self.getRuleCheckboxes():
            checkbox.stateChanged.connect(self.onFormChanged)

    def getFormState(self):
        state = (
            self.max_log_file_value.text().strip(),
            self.num_logs_value.text().strip(),
            self.space_left_value.text().strip(),
            self.admin_space_left_value.text().strip(),
            self.identity_audit_checkbox.isChecked(),
            self.audit_config_audit_checkbox.isChecked(),
            self.audit_log_read_checkbox.isChecked(),
            self.journald_config_audit_checkbox.isChecked(),
            self.password_policy_audit_checkbox.isChecked(),
            self.privileged_commands_audit_checkbox.isChecked(),
            self.network_config_audit_checkbox.isChecked(),
            self.kernel_module_audit_checkbox.isChecked(),
            self.system_power_audit_checkbox.isChecked(),
            self.account_modification_audit_checkbox.isChecked(),
            self.file_delete_audit_checkbox.isChecked(),
            self.mount_export_audit_checkbox.isChecked(),
            self.discretionary_access_audit_checkbox.isChecked(),
            self.unauthorized_access_audit_checkbox.isChecked(),
        )

        custom_state = []

        for item in self.custom_rules:
            custom_state.append((
                item["name"].strip(),
                item["rule"].strip(),
                item["checkbox"].isChecked(),
            ))

        return state + (tuple(custom_state),)

    def onFormChanged(self, *args):
        if self.form_loading:
            return

        self.updateApplyButton()

    def updateApplyButton(self):
        if self.btn_apply == None:
            return

        if self.proc_apply != None and self.proc_apply.state() != QProcess.ProcessState.NotRunning:
            self.btn_apply.setEnabled(False)
            return

        if self.initial_form_state == None:
            self.btn_apply.setEnabled(False)
            return

        self.btn_apply.setEnabled(self.getFormState() != self.initial_form_state)

    def updateAddRuleButton(self, *args):
        if self.btn_add_custom_rule == None:
            return

        if self.proc_save_custom != None and self.proc_save_custom.state() != QProcess.ProcessState.NotRunning:
            self.btn_add_custom_rule.setEnabled(False)
            return

        has_name = self.custom_rule_name.text().strip() != ""
        has_rule = self.custom_rule_text.toPlainText().strip() != ""
        self.btn_add_custom_rule.setEnabled(has_name and has_rule)

    def getExistingRuleNames(self):
        names = set()

        for checkbox in self.getRuleCheckboxes():
            names.add(checkbox.text().strip().casefold())

        for item in self.custom_rules:
            names.add(item["name"].strip().casefold())

        return names

    def validateCustomRuleName(self, name):
        value = name.strip()

        if not value:
            return False, self.tr("Enter a rule name")

        if value.casefold() in self.getExistingRuleNames():
            return False, self.tr("A rule with this name already exists")

        return True, ""

    def validateCustomRule(self, rule, check_duplicate = True):
        value = rule.strip()

        if not value:
            return False, self.tr("Enter a rule")

        lines = [line.strip() for line in value.splitlines() if line.strip()]

        for line in lines:
            parts = line.split()

            if len(parts) != 6 or parts[0] != "-w" or parts[2] != "-p" or parts[4] != "-k":
                return False, self.tr("Use the format: -w /path -p rwax -k key")

            path = parts[1]
            permissions = parts[3]
            key = parts[5]

            if not path.startswith("/") or not os.path.exists(path):
                return False, self.tr("The monitored path must be absolute and must exist")

            if not permissions or any(value not in "rwax" for value in permissions) or len(set(permissions)) != len(permissions):
                return False, self.tr("Permissions may contain only r, w, a and x")

            allowed_key_characters = "abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789_-"

            if len(key) > 31 or any(value not in allowed_key_characters for value in key):
                return False, self.tr("The key may contain up to 31 Latin letters, digits, _ and -")

        if check_duplicate:
            for item in self.custom_rules:
                if item["rule"].strip().casefold() == value.casefold():
                    return False, self.tr("A rule with this description already exists")

        return True, ""

    def addCustomRuleToList(self, name, rule, enabled = False):
        item_widget = QWidget()
        item_widget.setProperty("custom_rule", rule)
        item_widget.installEventFilter(self)
        item_widget.setCursor(Qt.CursorShape.PointingHandCursor)

        item_layout = QHBoxLayout(item_widget)
        item_layout.setContentsMargins(0, 0, 0, 0)

        checkbox = QCheckBox(name)
        checkbox.setCursor(Qt.CursorShape.PointingHandCursor)
        checkbox.setFocusPolicy(Qt.FocusPolicy.StrongFocus)
        checkbox.setChecked(enabled)
        checkbox.stateChanged.connect(self.onFormChanged)
        checkbox.clicked.connect(lambda checked, value=rule: self.showCustomRuleInfo(value))
        item_layout.addWidget(checkbox, 1)

        delete_button = QPushButton("×")
        delete_button.setFixedSize(24, 24)
        delete_button.setToolTip(self.tr("Delete rule"))
        delete_button.clicked.connect(lambda checked = False, widget = item_widget: self.deleteCustomRule(widget))
        item_layout.addWidget(delete_button)

        self.custom_rules_layout.addWidget(item_widget)
        self.custom_rules.append({
            "name": name,
            "rule": rule,
            "checkbox": checkbox,
            "widget": item_widget,
        })

        self.custom_rules_title.setVisible(True)
        self.custom_rules_widget.setVisible(True)

    def deleteCustomRule(self, widget):
        delete_item = None

        for item in self.custom_rules:
            if item["widget"] == widget:
                delete_item = item
                break

        if delete_item == None:
            return

        enabled = delete_item["checkbox"].isChecked()

        try:
            with open("/etc/altcenter/auditd_custom_enabled.rules", "r", encoding="utf-8", errors="replace") as f:
                enabled_lines = {line.strip() for line in f.read().splitlines() if line.strip()}
                rule_lines = [line.strip() for line in delete_item["rule"].splitlines() if line.strip()]
                enabled = enabled or (bool(rule_lines) and all(line in enabled_lines for line in rule_lines))
        except:
            pass

        if enabled:
            QMessageBox.information(
                self,
                self.tr("Active rule"),
                self.tr("Disable the rule and apply the changes before deleting it")
            )
            return

        custom_rules_data = []
        custom_enabled_rules = ""

        for item in self.custom_rules:
            if item == delete_item:
                continue

            custom_rules_data.append({
                "name": item["name"],
                "rule": item["rule"],
            })

            if item["checkbox"].isChecked():
                custom_enabled_rules += item["rule"].strip() + "\n"

        custom_rules_json = json.dumps(
            custom_rules_data,
            ensure_ascii=False,
            indent=2
        ) + "\n"

        custom_rules_json_base64 = base64.b64encode(
            custom_rules_json.encode("utf-8")
        ).decode("ascii")

        custom_enabled_rules_base64 = base64.b64encode(
            custom_enabled_rules.encode("utf-8")
        ).decode("ascii")

        name = delete_item["name"]
        rule = delete_item["rule"]

        self.lbl_custom_rule_status.setText(
            self.tr('Deleting rule "%s"') % name
        )

        cmd = (
            "mkdir -p /etc/altcenter /etc/audit/rules.d && "
            f"printf '%s' '{custom_rules_json_base64}' | base64 -d > /etc/altcenter/auditd_custom_rules.json && "
            "chmod 644 /etc/altcenter/auditd_custom_rules.json && "
            f"printf '%s' '{custom_enabled_rules_base64}' | base64 -d > /etc/audit/rules.d/71-altcenter-custom.rules && "
            "chmod 600 /etc/audit/rules.d/71-altcenter-custom.rules && "
            "if command -v augenrules >/dev/null 2>&1; then augenrules --load >/dev/null 2>&1; else exit 1; fi && "
            f"printf '%s' '{custom_enabled_rules_base64}' | base64 -d > /etc/altcenter/auditd_custom_enabled.rules && "
            "chmod 644 /etc/altcenter/auditd_custom_enabled.rules"
        )

        exit_code = QProcess.execute("pkexec", ["sh", "-c", cmd])

        if exit_code != 0:
            self.lbl_custom_rule_status.setText(self.tr("Failed"))
            return

        self.custom_rules.remove(delete_item)
        self.custom_rules_layout.removeWidget(delete_item["widget"])
        delete_item["widget"].deleteLater()

        if self.custom_rule_info_panel.toPlainText().strip() == rule.strip():
            self.custom_rule_info_panel.clear()
            self.custom_rule_info_panel.setVisible(False)

        if not self.custom_rules:
            self.custom_rules_title.setVisible(False)
            self.custom_rules_widget.setVisible(False)

        self.initial_form_state = self.getFormState()
        self.lbl_custom_rule_status.setText(
            self.tr('Rule "%s" deleted') % name
        )
        self.updateApplyButton()

    def eventFilter(self, watched, event):
        if (
            event.type() == QEvent.Type.MouseButtonPress
            and event.button() == Qt.MouseButton.LeftButton
        ):
            for item in self.custom_rules:
                if item["widget"] == watched:
                    item["checkbox"].setFocus(Qt.FocusReason.MouseFocusReason)
                    self.showCustomRuleInfo(item["rule"])
                    return True

        return super().eventFilter(watched, event)

    def showCustomRuleInfo(self, rule):
        self.custom_rule_info_panel.setPlainText(rule)
        self.custom_rule_info_panel.setVisible(True)
        
    def loadSavedCustomRules(self):
        path = "/etc/altcenter/auditd_custom_rules.json"
        enabled_path = "/etc/altcenter/auditd_custom_enabled.rules"

        try:
            with open(path, "r", encoding="utf-8", errors="replace") as f:
                data = json.load(f)
        except:
            return

        try:
            with open(enabled_path, "r", encoding="utf-8", errors="replace") as f:
                enabled_rules = f.read()
        except:
            enabled_rules = ""

        if not isinstance(data, list):
            return

        for item in data:
            if not isinstance(item, dict):
                continue

            name = str(item.get("name", "")).strip()
            rule = str(item.get("rule", "")).strip()

            if not name or not rule:
                continue

            if name.casefold() in self.getExistingRuleNames():
                continue

            duplicate_rule = False

            for current_item in self.custom_rules:
                if current_item["rule"].strip().casefold() == rule.casefold():
                    duplicate_rule = True
                    break

            if duplicate_rule:
                continue

            enabled_lines = {line.strip() for line in enabled_rules.splitlines() if line.strip()}
            rule_lines = [line.strip() for line in rule.splitlines() if line.strip()]
            enabled = bool(rule_lines) and all(line in enabled_lines for line in rule_lines)
            self.addCustomRuleToList(name, rule, enabled)

    def onAddCustomRuleClicked(self):
        if self.proc_save_custom != None and self.proc_save_custom.state() != QProcess.ProcessState.NotRunning:
            return

        name = self.custom_rule_name.text().strip()
        rule = self.custom_rule_text.toPlainText().strip()

        valid, error = self.validateCustomRuleName(name)
        if not valid:
            self.lbl_custom_rule_status.setText(error)
            return

        valid, error = self.validateCustomRule(rule)
        if not valid:
            self.lbl_custom_rule_status.setText(error)
            return

        custom_rules_data = []

        for item in self.custom_rules:
            custom_rules_data.append({
                "name": item["name"],
                "rule": item["rule"],
            })

        custom_rules_data.append({
            "name": name,
            "rule": rule,
        })

        custom_rules_json = json.dumps(
            custom_rules_data,
            ensure_ascii=False,
            indent=2
        ) + "\n"

        custom_rules_json_base64 = base64.b64encode(
            custom_rules_json.encode("utf-8")
        ).decode("ascii")

        cmd = (
            "mkdir -p /etc/altcenter && "
            f"printf '%s' '{custom_rules_json_base64}' | base64 -d > /etc/altcenter/auditd_custom_rules.json && "
            "chmod 644 /etc/altcenter/auditd_custom_rules.json"
        )

        self.pending_custom_rule = {
            "name": name,
            "rule": rule,
        }

        self.lbl_custom_rule_status.setText("")
        self.custom_rule_name.setEnabled(False)
        self.custom_rule_text.setEnabled(False)
        self.btn_add_custom_rule.setEnabled(False)

        self.proc_save_custom = QProcess(self)
        env = QProcessEnvironment.systemEnvironment()
        self.proc_save_custom.setProcessEnvironment(env)
        self.proc_save_custom.finished.connect(self.onSaveCustomRuleFinished)
        self.proc_save_custom.start("pkexec", ["sh", "-c", cmd])

    def onSaveCustomRuleFinished(self, exit_code, exit_status):
        err = self.proc_save_custom.readAllStandardError().data().decode(errors="replace").strip()

        self.custom_rule_name.setEnabled(True)
        self.custom_rule_text.setEnabled(True)

        if exit_code == 0 and self.pending_custom_rule != None:
            name = self.pending_custom_rule["name"]
            rule = self.pending_custom_rule["rule"]

            self.form_loading = True
            self.addCustomRuleToList(name, rule, False)

            if self.initial_form_state != None:
                saved_custom_state = list(self.initial_form_state[-1])
                saved_custom_state.append((name, rule, False))
                self.initial_form_state = self.initial_form_state[:-1] + (tuple(saved_custom_state),)
            else:
                self.initial_form_state = self.getFormState()

            self.form_loading = False

            self.custom_rule_name.setText("")
            self.custom_rule_text.setPlainText("")
            self.lbl_custom_rule_status.setText(self.tr("Rule saved"))
            self.pending_custom_rule = None
            self.updateAddRuleButton()
            self.updateApplyButton()
            return

        self.pending_custom_rule = None

        if err:
            self.lbl_custom_rule_status.setText(err)
        else:
            self.lbl_custom_rule_status.setText(self.tr("Failed"))

        self.updateAddRuleButton()

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
            self.system_power_audit_checkbox.setChecked(False)
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

        system_power_rule = self.hasAllExistingPaths(lines, [
            "/usr/bin/loginctl",
            "/bin/loginctl",
            "/usr/sbin/reboot",
            "/sbin/reboot",
            "/usr/sbin/poweroff",
            "/sbin/poweroff",
            "/usr/sbin/shutdown",
            "/sbin/shutdown",
            "/usr/sbin/halt",
            "/sbin/halt",
        ])

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
        self.system_power_audit_checkbox.setChecked(system_power_rule)
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
        if self.proc_apply != None and self.proc_apply.state() != QProcess.ProcessState.NotRunning:
            return

        if self.initial_form_state == None or self.getFormState() == self.initial_form_state:
            self.updateApplyButton()
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

        system_power_rules = ""
        if self.system_power_audit_checkbox.isChecked():
            system_power_rules = self.buildWatchRules(
                "system_power",
                "system_power",
                [
                    ("/usr/bin/loginctl", "x"),
                    ("/bin/loginctl", "x"),
                    ("/usr/sbin/reboot", "x"),
                    ("/sbin/reboot", "x"),
                    ("/usr/sbin/poweroff", "x"),
                    ("/sbin/poweroff", "x"),
                    ("/usr/sbin/shutdown", "x"),
                    ("/sbin/shutdown", "x"),
                    ("/usr/sbin/halt", "x"),
                    ("/sbin/halt", "x"),
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
            + system_power_rules
            + account_modification_rules
            + file_delete_rules
            + mount_export_rules
            + discretionary_access_rules
            + unauthorized_access_rules
        )
        managed_rules = managed_rules.replace("'", "'\"'\"'")

        custom_enabled_rules = ""

        for item in self.custom_rules:
            if item["checkbox"].isChecked():
                valid, error = self.validateCustomRule(item["rule"], False)

                if not valid:
                    self.lbl_status.setText(
                        self.tr('Rule "%s": %s') % (item["name"], error)
                    )
                    return

                custom_enabled_rules += item["rule"].strip() + "\n"

        custom_enabled_rules_base64 = base64.b64encode(
            custom_enabled_rules.encode("utf-8")
        ).decode("ascii")

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

        custom_rules_cmd = (
            "mkdir -p /etc/audit/rules.d /etc/altcenter && "
            f"printf '%s' '{custom_enabled_rules_base64}' | base64 -d > /etc/audit/rules.d/71-altcenter-custom.rules && "
            "chmod 600 /etc/audit/rules.d/71-altcenter-custom.rules"
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
            + custom_rules_cmd + " && "
            + "if command -v augenrules >/dev/null 2>&1; then augenrules --load; else exit 1; fi && "
            + f"printf '%s' '{custom_enabled_rules_base64}' | base64 -d > /etc/altcenter/auditd_custom_enabled.rules && "
            + "chmod 644 /etc/altcenter/auditd_custom_enabled.rules && "
            + "(cat /etc/audit/rules.d/*.rules > /tmp/altcenter_audit.rules 2>/dev/null && chmod 644 /tmp/altcenter_audit.rules 2>/dev/null || :) && "
            + "if command -v service >/dev/null 2>&1; then service auditd restart; else systemctl restart auditd; fi"
        )

        self.proc_apply = QProcess(self)
        env = QProcessEnvironment.systemEnvironment()
        self.proc_apply.setProcessEnvironment(env)
        self.proc_apply.finished.connect(self.on_apply_finished)
        self.proc_apply.start("pkexec", ["sh", "-c", cmd])

    def on_apply_finished(self, exit_code, exit_status):
        err = self.proc_apply.readAllStandardError().data().decode(errors="replace").strip()

        if exit_code == 0:
            self.lbl_status.setText(self.tr("Done"))

            self.form_loading = True
            self.loadSavedLimits()
            self.loadSavedRules()
            self.initial_form_state = self.getFormState()
            self.form_loading = False

            self.updateApplyButton()
            return

        if err:
            self.lbl_status.setText(err)
        else:
            self.lbl_status.setText(self.tr("Failed"))

        self.updateApplyButton()

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