from PyQt6.QtWidgets import QWidget, QVBoxLayout, QHBoxLayout, QStackedWidget, QListWidget, QListWidgetItem, QTextEdit, QSplitter, QLabel, QPushButton, QLineEdit, QComboBox, QToolButton, QCheckBox, QFileDialog
from PyQt6.QtGui import QStandardItem, QStandardItemModel, QFont, QTextCursor, QTextCharFormat, QColor, QPalette
from PyQt6.QtCore import Qt, QProcess, QProcessEnvironment, QLocale, QPoint

import plugins

class SSHSettingsWidget(QWidget):
    def __init__(self, main_window=None):
        super().__init__(main_window)

        self.main_window = main_window

        self.proc_apply = None

        self.root_login_check = None
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

    def loadSavedSettings(self):
        value = self.readSshdParameter("PermitRootLogin")
        self.root_login_check.setChecked(value == "no")

    def on_apply_clicked(self):
        if self.proc_apply != None and self.proc_apply.state() != QProcess.ProcessState.NotRunning:
            return

        value = "without-password"

        if self.root_login_check.isChecked():
            value = "no"

        self.lbl_status.setText("")
        self.btn_apply.setEnabled(False)

        cmd = (
            "conf=$(test -f /etc/openssh/sshd_config && echo /etc/openssh/sshd_config || echo /etc/ssh/sshd_config); "
            "cp -a \"$conf\" \"$conf.altcenter.bak\"; "
            "sed -i -E '/^[[:space:]]*#?[[:space:]]*PermitRootLogin([[:space:]]+|$)/Id' \"$conf\"; "
            f"echo 'PermitRootLogin {value}' >> \"$conf\"; "
            "cp \"$conf\" /tmp/altcenter_sshd_config; "
            "chmod 644 /tmp/altcenter_sshd_config; "
            "systemctl reload sshd || systemctl reload ssh || systemctl restart sshd || systemctl restart ssh"
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
            self.loadSavedSettings()
            return

        if err:
            self.lbl_status.setText(err)
        else:
            self.lbl_status.setText(self.tr("Failed"))


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