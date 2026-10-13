from PyQt6.QtWidgets import QWidget, QVBoxLayout, QHBoxLayout, QStackedWidget, QListWidget, QListWidgetItem, QTextEdit, QSplitter, QLabel, QPushButton, QLineEdit, QComboBox, QToolButton, QCheckBox, QFileDialog
from PyQt6.QtGui import QStandardItem, QStandardItemModel, QFont, QTextCursor, QTextCharFormat, QColor, QPalette
from PyQt6.QtCore import Qt, QProcess, QProcessEnvironment, QLocale, QPoint

import plugins

class SSHSettingsWidget(QWidget):
    def __init__(self, main_window=None):
        super().__init__(main_window)

        self.main_window = main_window

        self.proc_apply = None
        self.saved_settings = None

        self.root_login_check = None
        self.empty_passwords_check = None
        self.hostbased_authentication_check = None
        self.ignore_rhosts_check = None
        self.protocol_check = None
        self.allow_users_edit = None
        self.allow_groups_edit = None
        self.port_edit = None
        self.client_alive_interval_edit = None
        self.client_alive_count_max_edit = None
        self.btn_apply = None
        self.lbl_status = None

        self.initUI()
        self.loadSavedSettings()

    def initUI(self):
        layout = QVBoxLayout()

        layout.setContentsMargins(10, 10, 10, 10)

        root_login = QHBoxLayout()

        self.root_login_check = QCheckBox(self.tr("Deny remote SSH login as root"))
        root_login.addWidget(self.root_login_check)

        root_login.addStretch(1)

        layout.addLayout(root_login)

        empty_passwords = QHBoxLayout()

        self.empty_passwords_check = QCheckBox(self.tr("Deny SSH login with empty passwords"))
        empty_passwords.addWidget(self.empty_passwords_check)

        empty_passwords.addStretch(1)

        layout.addLayout(empty_passwords)

        hostbased_authentication = QHBoxLayout()

        self.hostbased_authentication_check = QCheckBox(self.tr("Disable SSH host-based authentication"))
        hostbased_authentication.addWidget(self.hostbased_authentication_check)

        hostbased_authentication.addStretch(1)

        layout.addLayout(hostbased_authentication)

        ignore_rhosts = QHBoxLayout()

        self.ignore_rhosts_check = QCheckBox(self.tr("Ignore .rhosts and .shosts files"))
        ignore_rhosts.addWidget(self.ignore_rhosts_check)

        ignore_rhosts.addStretch(1)

        layout.addLayout(ignore_rhosts)

        protocol = QHBoxLayout()

        self.protocol_check = QCheckBox(self.tr("Use SSH protocol version 2 only"))
        protocol.addWidget(self.protocol_check)

        protocol.addStretch(1)

        layout.addLayout(protocol)

        space = QLabel("")
        space.setWordWrap(True)

        layout.addWidget(space)

        access = QLabel(self.tr("Users and groups are separated by spaces, for example: user1 user2"))
        access.setWordWrap(True)

        layout.addWidget(access)

        allow_users_layout = QHBoxLayout()

        allow_users_label = QLabel(self.tr("Allowed SSH users"))
        allow_users_layout.addWidget(allow_users_label)

        self.allow_users_edit = QLineEdit()
        self.allow_users_edit.setMaximumWidth(300)
        allow_users_layout.addWidget(self.allow_users_edit)

        allow_users_layout.addStretch(1)

        layout.addLayout(allow_users_layout)

        allow_groups_layout = QHBoxLayout()

        allow_groups_label = QLabel(self.tr("Allowed SSH groups"))
        allow_groups_layout.addWidget(allow_groups_label)

        self.allow_groups_edit = QLineEdit()
        self.allow_groups_edit.setMaximumWidth(300)
        allow_groups_layout.addWidget(self.allow_groups_edit)

        allow_groups_layout.addStretch(1)

        layout.addLayout(allow_groups_layout)

        port_layout = QHBoxLayout()

        port_label = QLabel(self.tr("SSH port"))
        port_layout.addWidget(port_label)

        self.port_edit = QLineEdit()
        self.port_edit.setMaximumWidth(100)
        port_layout.addWidget(self.port_edit)

        port_layout.addStretch(1)

        layout.addLayout(port_layout)

        client_alive_interval_layout = QHBoxLayout()

        client_alive_interval_label = QLabel(self.tr("SSH inactivity timeout, sec."))
        client_alive_interval_layout.addWidget(client_alive_interval_label)

        self.client_alive_interval_edit = QLineEdit()
        self.client_alive_interval_edit.setMaximumWidth(100)
        client_alive_interval_layout.addWidget(self.client_alive_interval_edit)

        client_alive_interval_layout.addStretch(1)

        layout.addLayout(client_alive_interval_layout)

        client_alive_count_max_layout = QHBoxLayout()

        client_alive_count_max_label = QLabel(self.tr("SSH alive check count"))
        client_alive_count_max_layout.addWidget(client_alive_count_max_label)

        self.client_alive_count_max_edit = QLineEdit()
        self.client_alive_count_max_edit.setMaximumWidth(100)
        client_alive_count_max_layout.addWidget(self.client_alive_count_max_edit)

        client_alive_count_max_layout.addStretch(1)

        layout.addLayout(client_alive_count_max_layout)

        apply_layout = QHBoxLayout()

        self.btn_apply = QPushButton(self.tr("Apply"))
        self.btn_apply.clicked.connect(self.on_apply_clicked)
        apply_layout.addWidget(self.btn_apply)

        self.lbl_status = QLabel("")
        self.lbl_status.setTextInteractionFlags(Qt.TextInteractionFlag.TextSelectableByMouse)
        apply_layout.addWidget(self.lbl_status)

        apply_layout.addStretch(1)

        layout.addLayout(apply_layout)

        layout.addStretch(1)

        self.setLayout(layout)

        self.root_login_check.stateChanged.connect(self.updateApplyButton)
        self.empty_passwords_check.stateChanged.connect(self.updateApplyButton)
        self.hostbased_authentication_check.stateChanged.connect(self.updateApplyButton)
        self.ignore_rhosts_check.stateChanged.connect(self.updateApplyButton)
        self.protocol_check.stateChanged.connect(self.updateApplyButton)
        self.allow_users_edit.textChanged.connect(self.updateApplyButton)
        self.allow_groups_edit.textChanged.connect(self.updateApplyButton)
        self.port_edit.textChanged.connect(self.updateApplyButton)
        self.client_alive_interval_edit.textChanged.connect(self.updateApplyButton)
        self.client_alive_count_max_edit.textChanged.connect(self.updateApplyButton)

    def readSshdParameter(self, name):
        path = "/tmp/altcenter_sshd_config"

        try:
            with open(path, "r", encoding="utf-8", errors="replace") as f:
                lines = f.read().splitlines()
        except:
            return None

        for raw in lines:
            line = raw.strip()

            if not line or line.startswith("#"):
                continue

            parts = line.split(None, 1)

            if len(parts) != 2:
                continue

            if parts[0].lower() != name.lower():
                continue

            value = parts[1].split("#", 1)[0].strip()

            if not value:
                return None

            return value.split(None, 1)[0].lower()

        return None

    def readSshdParameterValue(self, name):
        path = "/tmp/altcenter_sshd_config"

        try:
            with open(path, "r", encoding="utf-8", errors="replace") as f:
                lines = f.read().splitlines()
        except:
            return None

        for raw in lines:
            line = raw.strip()

            if not line or line.startswith("#"):
                continue

            parts = line.split(None, 1)

            if len(parts) != 2:
                continue

            if parts[0].lower() != name.lower():
                continue

            value = parts[1].split("#", 1)[0].strip()

            if not value:
                return None

            return value

        return None

    def isValidSshListValue(self, value):
        allowed = "abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789_-.@*/?: "

        for char in value:
            if char not in allowed:
                return False

        return True

    def getCurrentSettings(self):
        return (
            self.root_login_check.isChecked(),
            self.empty_passwords_check.isChecked(),
            self.hostbased_authentication_check.isChecked(),
            self.ignore_rhosts_check.isChecked(),
            self.protocol_check.isChecked(),
            self.allow_users_edit.text().strip(),
            self.allow_groups_edit.text().strip(),
            self.port_edit.text().strip(),
            self.client_alive_interval_edit.text().strip(),
            self.client_alive_count_max_edit.text().strip()
        )

    def updateApplyButton(self, *args):
        if self.btn_apply == None:
            return

        if self.proc_apply != None and self.proc_apply.state() != QProcess.ProcessState.NotRunning:
            self.btn_apply.setEnabled(False)
            return

        if self.saved_settings == None:
            self.btn_apply.setEnabled(False)
            return

        self.btn_apply.setEnabled(self.getCurrentSettings() != self.saved_settings)

    def loadSavedSettings(self):
        value = self.readSshdParameter("PermitRootLogin")
        self.root_login_check.setChecked(value == "no")

        empty_passwords = self.readSshdParameter("PermitEmptyPasswords")
        self.empty_passwords_check.setChecked(empty_passwords != "yes")

        hostbased_authentication = self.readSshdParameter("HostbasedAuthentication")
        self.hostbased_authentication_check.setChecked(hostbased_authentication != "yes")

        ignore_rhosts = self.readSshdParameter("IgnoreRhosts")
        self.ignore_rhosts_check.setChecked(ignore_rhosts != "no")

        protocol = self.readSshdParameter("Protocol")
        self.protocol_check.setChecked(protocol == "2")

        allow_users = self.readSshdParameterValue("AllowUsers")

        if allow_users:
            self.allow_users_edit.setText(allow_users)
        else:
            self.allow_users_edit.setText("")

        allow_groups = self.readSshdParameterValue("AllowGroups")

        if allow_groups:
            self.allow_groups_edit.setText(allow_groups)
        else:
            self.allow_groups_edit.setText("")

        port = self.readSshdParameter("Port")

        if port:
            self.port_edit.setText(port)
        else:
            self.port_edit.setText("22")

        client_alive_interval = self.readSshdParameter("ClientAliveInterval")

        if client_alive_interval:
            self.client_alive_interval_edit.setText(client_alive_interval)
        else:
            self.client_alive_interval_edit.setText("0")

        client_alive_count_max = self.readSshdParameter("ClientAliveCountMax")

        if client_alive_count_max:
            self.client_alive_count_max_edit.setText(client_alive_count_max)
        else:
            self.client_alive_count_max_edit.setText("3")

        self.saved_settings = self.getCurrentSettings()
        self.updateApplyButton()

    def on_apply_clicked(self):
        if self.proc_apply != None and self.proc_apply.state() != QProcess.ProcessState.NotRunning:
            return

        if self.saved_settings != None and self.getCurrentSettings() == self.saved_settings:
            return

        value = "without-password"

        if self.root_login_check.isChecked():
            value = "no"

        empty_passwords = "yes"

        if self.empty_passwords_check.isChecked():
            empty_passwords = "no"

        hostbased_authentication = "yes"

        if self.hostbased_authentication_check.isChecked():
            hostbased_authentication = "no"

        ignore_rhosts = "no"

        if self.ignore_rhosts_check.isChecked():
            ignore_rhosts = "yes"

        allow_users = self.allow_users_edit.text().strip()

        if allow_users and not self.isValidSshListValue(allow_users):
            self.lbl_status.setText(self.tr("Invalid SSH users list. Use spaces only"))
            return

        allow_groups = self.allow_groups_edit.text().strip()

        if allow_groups and not self.isValidSshListValue(allow_groups):
            self.lbl_status.setText(self.tr("Invalid SSH groups list. Use spaces only"))
            return

        port = self.port_edit.text().strip()

        if not port:
            port = "22"

        if not port.isdigit() or int(port) < 1 or int(port) > 65535:
            self.lbl_status.setText(self.tr("Invalid SSH port"))
            return

        client_alive_interval = self.client_alive_interval_edit.text().strip()

        if not client_alive_interval:
            client_alive_interval = "0"

        if not client_alive_interval.isdigit():
            self.lbl_status.setText(self.tr("Invalid SSH session timeout"))
            return

        client_alive_count_max = self.client_alive_count_max_edit.text().strip()

        if not client_alive_count_max:
            client_alive_count_max = "3"

        if not client_alive_count_max.isdigit():
            self.lbl_status.setText(self.tr("Invalid SSH alive check count"))
            return

        self.lbl_status.setText("")
        self.btn_apply.setEnabled(False)

        cmd = (
            "conf=$(test -f /etc/openssh/sshd_config && echo /etc/openssh/sshd_config || echo /etc/ssh/sshd_config); "
            "cp -a \"$conf\" \"$conf.altcenter.bak\"; "
            "sed -i -E '/^[[:space:]]*#?[[:space:]]*PermitRootLogin([[:space:]]+|$)/Id' \"$conf\"; "
            f"echo 'PermitRootLogin {value}' >> \"$conf\"; "
            "sed -i -E '/^[[:space:]]*#?[[:space:]]*PermitEmptyPasswords([[:space:]]+|$)/Id' \"$conf\"; "
            f"echo 'PermitEmptyPasswords {empty_passwords}' >> \"$conf\"; "
            "sed -i -E '/^[[:space:]]*#?[[:space:]]*HostbasedAuthentication([[:space:]]+|$)/Id' \"$conf\"; "
            f"echo 'HostbasedAuthentication {hostbased_authentication}' >> \"$conf\"; "
            "sed -i -E '/^[[:space:]]*#?[[:space:]]*IgnoreRhosts([[:space:]]+|$)/Id' \"$conf\"; "
            f"echo 'IgnoreRhosts {ignore_rhosts}' >> \"$conf\"; "
            "sed -i -E '/^[[:space:]]*#?[[:space:]]*Protocol([[:space:]]+|$)/Id' \"$conf\"; "
        )

        if self.protocol_check.isChecked():
            cmd += "echo 'Protocol 2' >> \"$conf\"; "

        cmd += (
            "sed -i -E '/^[[:space:]]*#?[[:space:]]*AllowUsers([[:space:]]+|$)/Id' \"$conf\"; "
        )

        if allow_users:
            cmd += f"echo 'AllowUsers {allow_users}' >> \"$conf\"; "

        cmd += (
            "sed -i -E '/^[[:space:]]*#?[[:space:]]*AllowGroups([[:space:]]+|$)/Id' \"$conf\"; "
        )

        if allow_groups:
            cmd += f"echo 'AllowGroups {allow_groups}' >> \"$conf\"; "

        cmd += (
            "sed -i -E '/^[[:space:]]*#?[[:space:]]*Port([[:space:]]+|$)/Id' \"$conf\"; "
            f"echo 'Port {port}' >> \"$conf\"; "
            "sed -i -E '/^[[:space:]]*#?[[:space:]]*ClientAliveInterval([[:space:]]+|$)/Id' \"$conf\"; "
            f"echo 'ClientAliveInterval {client_alive_interval}' >> \"$conf\"; "
            "sed -i -E '/^[[:space:]]*#?[[:space:]]*ClientAliveCountMax([[:space:]]+|$)/Id' \"$conf\"; "
            f"echo 'ClientAliveCountMax {client_alive_count_max}' >> \"$conf\"; "
            "chown root:root \"$conf\"; "
            "chmod 644 \"$conf\"; "
            "if ! sshd -t -f \"$conf\"; then cp -a \"$conf.altcenter.bak\" \"$conf\"; exit 1; fi; "
            "cp \"$conf\" /tmp/altcenter_sshd_config && "
            "chmod 644 /tmp/altcenter_sshd_config && "
            "(systemctl reload sshd || systemctl reload ssh || systemctl restart sshd || systemctl restart ssh)"
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
            self.loadSavedSettings()
            return

        if err:
            self.lbl_status.setText(err)
        else:
            self.lbl_status.setText(self.tr("Failed"))

        self.updateApplyButton()


class PluginSSHSettings(plugins.Base):
    requires_admin = True
    def __init__(self, plist: QStandardItemModel=None, pane: QStackedWidget = None):
        super().__init__("ssh_settings", 150, plist, pane)

        if self.plist != None and self.pane != None:
            self.node = QStandardItem(self.tr("SSH settings"))
            self.node.setData(self.name)
            self.add_to_menu(self.node)
            self.pane.addWidget(QWidget())

    def _do_start(self, idx: int):
        main_window = self.pane.window()
        main_widget = SSHSettingsWidget(main_window)
        self.pane.insertWidget(idx, main_widget)