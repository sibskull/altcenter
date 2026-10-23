import base64
import os
import pwd
import stat
import sys
import shlex


def install_ssh_key(username, key):
    key = key.strip()
    parts = key.split()
    types = ("ssh-ed25519", "ssh-rsa", "ecdsa-sha2-nistp256", "ecdsa-sha2-nistp384", "ecdsa-sha2-nistp521", "sk-ssh-ed25519@openssh.com", "sk-ecdsa-sha2-nistp256@openssh.com")
    if len(parts) < 2 or parts[0] not in types or len(key) > 16384 or any(ord(char) < 32 for char in key):
        sys.exit("Invalid public SSH key")
    try:
        decoded = base64.b64decode(parts[1], validate=True)
        length = int.from_bytes(decoded[:4], "big")
        if length < 1 or length > 100 or decoded[4:4 + length].decode("ascii") != parts[0]:
            raise ValueError()
    except (ValueError, UnicodeError):
        sys.exit("Invalid public SSH key")
    account = pwd.getpwnam(username)
    if account.pw_uid < 1000 or account.pw_uid >= 60000 or not os.path.isabs(account.pw_dir) or account.pw_dir == "/":
        sys.exit("Invalid SSH user")
    home_fd = os.open(account.pw_dir, os.O_RDONLY | os.O_DIRECTORY | os.O_NOFOLLOW)
    try:
        home_info = os.fstat(home_fd)
        if home_info.st_uid not in (0, account.pw_uid) or home_info.st_mode & 0o022:
            sys.exit("Unsafe home directory")
        try:
            ssh_fd = os.open(".ssh", os.O_RDONLY | os.O_DIRECTORY | os.O_NOFOLLOW, dir_fd=home_fd)
        except FileNotFoundError:
            os.mkdir(".ssh", 0o700, dir_fd=home_fd)
            ssh_fd = os.open(".ssh", os.O_RDONLY | os.O_DIRECTORY | os.O_NOFOLLOW, dir_fd=home_fd)
            os.fchown(ssh_fd, account.pw_uid, account.pw_gid)
        try:
            if os.fstat(ssh_fd).st_uid != account.pw_uid:
                sys.exit("Unsafe .ssh directory owner")
            os.fchmod(ssh_fd, 0o700)
            try:
                key_fd = os.open("authorized_keys", os.O_RDWR | os.O_APPEND | os.O_NOFOLLOW, dir_fd=ssh_fd)
            except FileNotFoundError:
                key_fd = os.open("authorized_keys", os.O_RDWR | os.O_APPEND | os.O_CREAT | os.O_EXCL | os.O_NOFOLLOW, 0o600, dir_fd=ssh_fd)
                os.fchown(key_fd, account.pw_uid, account.pw_gid)
            try:
                info = os.fstat(key_fd)
                if not stat.S_ISREG(info.st_mode) or info.st_uid != account.pw_uid or info.st_nlink != 1:
                    sys.exit("Unsafe authorized_keys file")
                os.fchmod(key_fd, 0o600)
                existing = os.read(key_fd, 4194305)
                if len(existing) > 4194304:
                    sys.exit("authorized_keys file is too large")
                name = parts[0].encode("ascii")
                data = parts[1].encode("ascii")
                for line in existing.splitlines():
                    tokens = line.split()
                    if any(tokens[index:index + 2] == [name, data] for index in range(len(tokens) - 1)):
                        print("exists")
                        sys.exit(0)
                addition = (b"" if not existing or existing.endswith(b"\n") else b"\n") + key.encode("utf-8") + b"\n"
                while addition:
                    addition = addition[os.write(key_fd, addition):]
                os.fsync(key_fd)
                print("added")
            finally:
                os.close(key_fd)
        finally:
            os.close(ssh_fd)
    finally:
        os.close(home_fd)


if __name__ == "__main__":
    if len(sys.argv) != 4 or sys.argv[1] != "--install-ssh-key" or os.geteuid() != 0:
        sys.exit(2)
    install_ssh_key(sys.argv[2], sys.argv[3])
    sys.exit(0)


from PyQt6.QtWidgets import QWidget, QVBoxLayout, QHBoxLayout, QStackedWidget, QListWidget, QListWidgetItem, QTextEdit, QSplitter, QLabel, QPushButton, QLineEdit, QComboBox, QToolButton, QCheckBox, QFileDialog, QScrollArea, QFrame
from PyQt6.QtGui import QStandardItem, QStandardItemModel, QFont, QTextCursor, QTextCharFormat, QColor, QPalette
from PyQt6.QtCore import Qt, QProcess, QProcessEnvironment, QLocale, QPoint

import plugins
from my_utils import get_local_users



class SSHSettingsWidget(QWidget):
    def __init__(self, main_window=None):
        super().__init__(main_window)

        self.main_window = main_window

        self.proc_apply = None
        self.proc_key = None
        self.saved_settings = None

        self.root_login_check = None
        self.pubkey_authentication_check = None
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
        root_layout = QVBoxLayout(self)
        root_layout.setContentsMargins(0, 0, 0, 0)

        self.scroll = QScrollArea()
        self.scroll.setWidgetResizable(True)
        self.scroll.setFrameShape(QFrame.Shape.NoFrame)
        self.scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        root_layout.addWidget(self.scroll)

        content = QWidget()
        layout = QVBoxLayout(content)
        layout.setContentsMargins(10, 10, 10, 10)

        key_user_layout = QHBoxLayout()
        key_user_layout.addWidget(QLabel(self.tr("SSH user")))
        self.key_user_combo = QComboBox()
        self.key_user_combo.setMaximumWidth(300)
        self.key_user_combo.addItem(self.tr("Select a user"), "")
        for name, uid in get_local_users(min_uid=1000, max_uid=60000):
            self.key_user_combo.addItem(f"{name} (uid {uid})", name)
        key_user_layout.addWidget(self.key_user_combo)
        key_user_layout.addStretch(1)
        layout.addLayout(key_user_layout)

        layout.addWidget(QLabel(self.tr("Public SSH key")))
        self.key_edit = QTextEdit()
        self.key_edit.setPlaceholderText(self.tr("Paste your public SSH key here"))
        self.key_edit.setMaximumHeight(85)
        layout.addWidget(self.key_edit)

        key_action_layout = QHBoxLayout()
        self.btn_add_key = QPushButton(self.tr("Add public key"))
        self.btn_add_key.setEnabled(False)
        key_action_layout.addWidget(self.btn_add_key)
        self.lbl_key_status = QLabel("")
        self.lbl_key_status.setWordWrap(True)
        key_action_layout.addWidget(self.lbl_key_status)
        key_action_layout.addStretch(1)
        layout.addLayout(key_action_layout)

        self.btn_add_key.clicked.connect(self.on_add_key_clicked)
        self.key_user_combo.currentIndexChanged.connect(self.updateAddKeyButton)
        self.key_edit.textChanged.connect(self.updateAddKeyButton)

        pubkey_authentication = QHBoxLayout()

        self.pubkey_authentication_check = QCheckBox(self.tr("Allow SSH login using a key"))
        pubkey_authentication.addWidget(self.pubkey_authentication_check)

        pubkey_authentication.addStretch(1)

        layout.addLayout(pubkey_authentication)

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

        self.scroll.setWidget(content)

        self.root_login_check.stateChanged.connect(self.updateApplyButton)
        self.pubkey_authentication_check.stateChanged.connect(self.updateApplyButton)
        self.empty_passwords_check.stateChanged.connect(self.updateApplyButton)
        self.hostbased_authentication_check.stateChanged.connect(self.updateApplyButton)
        self.ignore_rhosts_check.stateChanged.connect(self.updateApplyButton)
        self.protocol_check.stateChanged.connect(self.updateApplyButton)
        self.allow_users_edit.textChanged.connect(self.updateApplyButton)
        self.allow_groups_edit.textChanged.connect(self.updateApplyButton)
        self.port_edit.textChanged.connect(self.updateApplyButton)
        self.client_alive_interval_edit.textChanged.connect(self.updateApplyButton)
        self.client_alive_count_max_edit.textChanged.connect(self.updateApplyButton)

    def updateAddKeyButton(self, *args):
        running = self.proc_key is not None and self.proc_key.state() != QProcess.ProcessState.NotRunning
        self.btn_add_key.setEnabled(bool(self.key_user_combo.currentData() and self.key_edit.toPlainText().strip()) and not running)

    def on_add_key_clicked(self):
        if self.proc_key is not None and self.proc_key.state() != QProcess.ProcessState.NotRunning:
            return

        username = self.key_user_combo.currentData()
        key = self.key_edit.toPlainText().strip()
        parts = key.split()
        types = ("ssh-ed25519", "ssh-rsa", "ecdsa-sha2-nistp256", "ecdsa-sha2-nistp384", "ecdsa-sha2-nistp521", "sk-ssh-ed25519@openssh.com", "sk-ecdsa-sha2-nistp256@openssh.com")
        if not username or len(parts) < 2 or parts[0] not in types or len(key) > 16384 or any(ord(char) < 32 for char in key):
            self.lbl_key_status.setText(self.tr("Invalid SSH public key or user."))
            return
        try:
            decoded = base64.b64decode(parts[1], validate=True)
            length = int.from_bytes(decoded[:4], "big")
            if length < 1 or length > 100 or decoded[4:4 + length].decode("ascii") != parts[0]:
                raise ValueError()
        except (ValueError, UnicodeError):
            self.lbl_key_status.setText(self.tr("Invalid SSH public key or user."))
            return

        self.lbl_key_status.setText(self.tr("Adding SSH key..."))
        self.btn_add_key.setEnabled(False)
        self.key_user_combo.setEnabled(False)
        self.key_edit.setEnabled(False)
        self.proc_key = QProcess(self)
        self.proc_key.setProcessEnvironment(QProcessEnvironment.systemEnvironment())
        self.proc_key.finished.connect(self.on_add_key_finished)
        self.proc_key.errorOccurred.connect(self.on_add_key_error)
        self.proc_key.start("pkexec", ["/usr/bin/python3", os.path.realpath(__file__), "--install-ssh-key", username, key])

    def on_add_key_error(self, error):
        if self.proc_key is not None and self.proc_key.state() == QProcess.ProcessState.NotRunning:
            self.lbl_key_status.setText(self.tr("Failed to start the privileged process."))
            self.key_user_combo.setEnabled(True)
            self.key_edit.setEnabled(True)
            self.updateAddKeyButton()

    def on_add_key_finished(self, exit_code, exit_status):
        output = self.proc_key.readAllStandardOutput().data().decode("utf-8", errors="replace").strip()
        error = self.proc_key.readAllStandardError().data().decode("utf-8", errors="replace").strip()
        self.key_user_combo.setEnabled(True)
        self.key_edit.setEnabled(True)

        if exit_code == 0 and exit_status == QProcess.ExitStatus.NormalExit:
            if output == "exists":
                self.lbl_key_status.setText(self.tr("This public key is already installed."))
            else:
                self.lbl_key_status.setText(self.tr("Public SSH key added."))
                self.key_edit.clear()
        else:
            errors = {
                "Invalid public SSH key": self.tr("Invalid public SSH key"),
                "Invalid SSH user": self.tr("Invalid SSH user"),
                "Unsafe home directory": self.tr("Unsafe home directory"),
                "Unsafe .ssh directory owner": self.tr("Unsafe .ssh directory owner"),
                "Unsafe authorized_keys file": self.tr("Unsafe authorized_keys file"),
                "authorized_keys file is too large": self.tr("authorized_keys file is too large")
            }
            self.lbl_key_status.setText(errors.get(error, error or self.tr("Failed to add the public SSH key.")))
        self.proc_key.deleteLater()
        self.proc_key = None
        self.updateAddKeyButton()

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

            if parts[0].lower() == "match":
                break

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

            if parts[0].lower() == "match":
                break

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
            self.pubkey_authentication_check.isChecked(),
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

        pubkey_authentication = self.readSshdParameter("PubkeyAuthentication")
        self.pubkey_authentication_check.setChecked(pubkey_authentication != "no")

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

        pubkey_authentication = "yes"

        if not self.pubkey_authentication_check.isChecked():
            pubkey_authentication = "no"

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

        updates = [
            f"PermitRootLogin {value}",
            f"PubkeyAuthentication {pubkey_authentication}",
            f"PermitEmptyPasswords {empty_passwords}",
            f"HostbasedAuthentication {hostbased_authentication}",
            f"IgnoreRhosts {ignore_rhosts}"
        ]

        if self.protocol_check.isChecked():
            updates.append("Protocol 2")

        if allow_users:
            updates.append(f"AllowUsers {allow_users}")

        if allow_groups:
            updates.append(f"AllowGroups {allow_groups}")

        updates.extend([
            f"Port {port}",
            f"ClientAliveInterval {client_alive_interval}",
            f"ClientAliveCountMax {client_alive_count_max}"
        ])

        cmd = (
            "set -e; "
            "conf=$(test -f /etc/openssh/sshd_config && echo /etc/openssh/sshd_config || echo /etc/ssh/sshd_config); "
            "tmp=$(mktemp \"${conf}.altcenter.XXXXXX\"); "
            "trap 'rm -f \"$tmp\"' EXIT; "
            "awk -v updates=" + shlex.quote("\n".join(updates)) + " '"
            "{ "
            "line = $0; sub(/^[[:space:]]*/, \"\", line); "
            "split(line, parts, /[[:space:]]+/); "
            "keyword = tolower(parts[1]); "
            "if (!inserted && line != \"\" && substr(line, 1, 1) != \"#\") { print updates; inserted = 1; } "
            "if (keyword == \"match\") in_match = 1; "
            "if (!in_match && (keyword == \"permitrootlogin\" || keyword == \"pubkeyauthentication\" || "
            "keyword == \"permitemptypasswords\" || keyword == \"hostbasedauthentication\" || "
            "keyword == \"ignorerhosts\" || keyword == \"protocol\" || "
            "keyword == \"allowusers\" || keyword == \"allowgroups\" || "
            "keyword == \"port\" || keyword == \"clientaliveinterval\" || "
            "keyword == \"clientalivecountmax\")) next; "
            "print; "
            "} "
            "END { if (!inserted) print updates; }"
            "' \"$conf\" > \"$tmp\"; "
            "chown root:root \"$tmp\"; "
            "chmod 644 \"$tmp\"; "
            "sshd -t -f \"$tmp\"; "
            "mv -f \"$tmp\" \"$conf\"; "
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
