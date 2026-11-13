#!/usr/bin/python3

import os
import re
import shutil
import subprocess
import secrets
import string
import ctypes
import ctypes.util
import grp
import pwd
import shlex
from pathlib import Path

from typing import Tuple, List, Optional

from PyQt6.QtCore import Qt
from PyQt6.QtGui import QStandardItem, QFont
from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QLabel,
    QHBoxLayout, QPushButton, QMessageBox, QStackedWidget, QListWidget,
    QListWidgetItem, QLineEdit, QApplication
)

import plugins
from my_utils import get_local_users


class ChangePassword(QWidget):
    def __init__(self, palette=None):
        super().__init__()
        if palette:
            self.setPalette(palette)
        self._active_user: Optional[str] = None
        self._build_ui()
        self._reload_users()

    def _build_ui(self) -> None:
        v = QVBoxLayout(self)

        title = QLabel(self.tr("Change password"))
        f = QFont()
        f.setBold(True)
        title.setFont(f)
        v.addWidget(title)

        v.addWidget(QLabel(self.tr("Users:")))
        self.list_users = QListWidget()
        self.list_users.setSelectionMode(QListWidget.SelectionMode.MultiSelection)
        v.addWidget(self.list_users, 1)

        self.lbl_active = QLabel(self.tr("Active user: -"))
        fb = QFont()
        fb.setBold(True)
        self.lbl_active.setFont(fb)
        self.lbl_active.setWordWrap(True)
        v.addWidget(self.lbl_active)

        row = QHBoxLayout()

        self.ed_new = QLineEdit()
        self.ed_new.setEchoMode(QLineEdit.EchoMode.Password)
        self.ed_new.setPlaceholderText(self.tr("Enter new password"))
        row.addWidget(self.ed_new, 1)

        self.btn_copy = QPushButton(self.tr("Copy"))
        self.btn_show = QPushButton(self.tr("Show"))
        self.btn_gen = QPushButton(self.tr("Generate"))
        self.btn_change = QPushButton(self.tr("Change"))

        row.addWidget(self.btn_copy)
        row.addWidget(self.btn_show)
        row.addWidget(self.btn_gen)
        row.addWidget(self.btn_change)

        v.addLayout(row)
        v.addStretch(1)

        self.btn_gen.clicked.connect(self._on_generate)
        self.btn_copy.clicked.connect(self._on_copy)
        self.btn_show.clicked.connect(self._on_toggle_show)
        self.btn_change.clicked.connect(self._on_change_password)
        self.list_users.itemSelectionChanged.connect(self._on_users_selection_changed)

    def _is_root(self) -> bool:
        try:
            return os.geteuid() == 0
        except Exception:
            return False

    def _selected_users(self) -> List[str]:
        out: List[str] = []
        for it in self.list_users.selectedItems():
            u = it.data(Qt.ItemDataRole.UserRole)
            if u:
                out.append(str(u))
        return sorted(set(out))

    def _reload_users(self):
        self.list_users.clear()

        for name, uid in get_local_users():
            it = QListWidgetItem(f"{name} (uid {uid})")
            it.setData(Qt.ItemDataRole.UserRole, name)
            self.list_users.addItem(it)

        if self.list_users.count() > 0:
            self.list_users.item(0).setSelected(True)
        self._on_users_selection_changed()

    def _on_users_selection_changed(self):
        items = self.list_users.selectedItems()
        if not items:
            self._active_user = None
            self.lbl_active.setText(self.tr("Active user: -"))
            return
        last = items[-1]
        self._active_user = str(last.data(Qt.ItemDataRole.UserRole))
        users = [str(it.data(Qt.ItemDataRole.UserRole)) for it in items if it.data(Qt.ItemDataRole.UserRole)]
        self.lbl_active.setText(self.tr("Active user: ") + ", ".join(users))

    def _passwdqc_enforce_mode(self):
        try:
            passwd = Path("/etc/pam.d/passwd").read_text(encoding="utf-8")
            system = Path("/etc/pam.d/system-auth").read_text(encoding="utf-8")
            local = Path("/etc/pam.d/system-auth-local-only").read_text(encoding="utf-8")
        except (OSError, UnicodeError):
            return None

        include_local = r"^\s*password\s+include\s+system-auth-local-only\s*$"
        include_system = r"^\s*password\s+include\s+system-auth\s*$"
        active = re.search(include_local, passwd, re.MULTILINE | re.IGNORECASE) or (
            re.search(include_system, passwd, re.MULTILINE | re.IGNORECASE) and
            re.search(include_local, system, re.MULTILINE | re.IGNORECASE)
        )
        if not active:
            return None

        lines = re.findall(
            r"^\s*password\s+\S+\s+pam_passwdqc\.so\b[^\n]*",
            local, re.MULTILINE | re.IGNORECASE
        )
        if len(lines) != 1 or "config=/etc/passwdqc.conf" not in lines[0].split():
            return None

        match = re.search(r"\benforce=([^\s]+)", lines[0], re.IGNORECASE)
        mode = match.group(1).lower() if match else "everyone"
        return mode if mode in ("none", "users", "everyone") else None

    def _read_passwdqc_config(self):
        try:
            text = Path("/etc/passwdqc.conf").read_text(encoding="utf-8")
            options = dict(re.findall(r"^\s*(min|max)\s*=\s*([^\s#]+)", text, re.MULTILINE))
            values = options["min"].split(",")
            if len(values) != 5:
                raise ValueError
            min_n1 = None if values[1].strip().lower() == "disabled" else int(values[1])
            max_length = int(options.get("max", "72"))
            if min_n1 is None or not 6 <= min_n1 <= 72 or min_n1 > max_length:
                raise ValueError
            if not 8 <= max_length <= 1024:
                raise ValueError
            return min_n1, max_length
        except (OSError, UnicodeError, KeyError, ValueError):
            raise RuntimeError(self.tr("Unable to read or parse the passwdqc configuration."))

    def _check_passwdqc_password(self, password, user):
        executable = shutil.which("pwqcheck") or "/usr/bin/pwqcheck"
        if not os.path.isfile(executable) or not os.access(executable, os.X_OK):
            return None
        if "\n" in password or "\r" in password or "\0" in password:
            return False
        try:
            result = subprocess.run(
                [executable, "config=/etc/passwdqc.conf"],
                input=f"{password}\n\n{user}\n".encode("utf-8"),
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                check=False,
                timeout=5
            )
        except (OSError, subprocess.TimeoutExpired):
            return None

        output = (result.stdout or b"").decode("utf-8", errors="replace").strip()
        if result.returncode == 0 and output == "OK":
            return True
        return False if output.startswith("Bad passphrase (") else None

    def _pam_password_module_entries(self, service, stack=None):
        stack = set() if stack is None else stack
        if service in stack or len(stack) >= 16:
            raise RuntimeError(self.tr("Unable to verify the password against the active password policy."))
        if not re.fullmatch(r"[A-Za-z0-9_.-]+", service):
            raise RuntimeError(self.tr("Unable to verify the password against the active password policy."))

        path = Path("/etc/pam.d") / service
        try:
            text = path.read_text(encoding="utf-8")
        except (OSError, UnicodeError):
            raise RuntimeError(self.tr("Unable to verify the password against the active password policy."))

        next_stack = stack | {service}
        entries = []
        for line in text.splitlines():
            try:
                tokens = shlex.split(line, comments=True)
            except ValueError:
                raise RuntimeError(self.tr("Unable to verify the password against the active password policy."))
            if not tokens:
                continue

            if tokens[0].lower() == "@include":
                if len(tokens) != 2:
                    raise RuntimeError(self.tr("Unable to verify the password against the active password policy."))
                entries.extend(self._pam_password_module_entries(tokens[1], next_stack))
                continue

            if tokens[0].lower() != "password" or len(tokens) < 3:
                continue

            if tokens[1].lower() in ("include", "substack"):
                entries.extend(self._pam_password_module_entries(tokens[2], next_stack))
                continue

            module = Path(tokens[2].lstrip("-")).name
            if module == "pam_pwquality.so":
                entries.append((path, tokens[3:]))

        return entries

    def _user_group_names(self, user):
        try:
            account = pwd.getpwnam(user)
            gids = set(os.getgrouplist(user, account.pw_gid))
            return {entry.gr_name for entry in grp.getgrall() if entry.gr_gid in gids}
        except (OSError, KeyError):
            raise RuntimeError(self.tr("Unable to verify the password against the active password policy."))

    def _pwquality_group_options(self, text, user):
        begin_marker = "# ALT Center group password policies begin"
        end_marker = "# ALT Center group password policies end"
        lines = text.splitlines()
        begins = [index for index, line in enumerate(lines) if line.strip() == begin_marker]
        ends = [index for index, line in enumerate(lines) if line.strip() == end_marker]
        if not begins and not ends:
            return None
        if len(begins) != 1 or len(ends) != 1 or begins[0] >= ends[0]:
            raise RuntimeError(self.tr("Unable to verify the password against the active password policy."))

        block = [line.strip() for line in lines[begins[0] + 1:ends[0]]]
        if len(block) < 2 or (len(block) - 2) % 4:
            raise RuntimeError(self.tr("Unable to verify the password against the active password policy."))

        group_count = (len(block) - 2) // 4
        user_groups = self._user_group_names(user)
        for index in range(group_count):
            gate, quality, history, exit_gate = block[index * 4:index * 4 + 4]
            match = re.fullmatch(
                r"password\s+\[success=ignore auth_err=3 default=die\]\s+"
                r"pam_succeed_if\.so\s+quiet\s+user\s+ingroup\s+([A-Za-z_][A-Za-z0-9_.-]*)",
                gate,
                re.IGNORECASE
            )
            if not match:
                raise RuntimeError(self.tr("Unable to verify the password against the active password policy."))

            group_name = match.group(1)
            expected_skip = (group_count - index - 1) * 4 + 2
            expected_exit = (
                f"password [success={expected_skip} default=die] "
                f"pam_succeed_if.so quiet user ingroup {group_name}"
            )
            if exit_gate != expected_exit:
                raise RuntimeError(self.tr("Unable to verify the password against the active password policy."))

            if group_name in user_groups:
                try:
                    tokens = shlex.split(quality, comments=True)
                except ValueError:
                    raise RuntimeError(self.tr("Unable to verify the password against the active password policy."))
                if len(tokens) < 3 or Path(tokens[2].lstrip("-")).name != "pam_pwquality.so":
                    raise RuntimeError(self.tr("Unable to verify the password against the active password policy."))
                return tokens[3:]

        try:
            tokens = shlex.split(block[-2], comments=True)
        except ValueError:
            raise RuntimeError(self.tr("Unable to verify the password against the active password policy."))
        if len(tokens) < 3 or Path(tokens[2].lstrip("-")).name != "pam_pwquality.so":
            raise RuntimeError(self.tr("Unable to verify the password against the active password policy."))
        return tokens[3:]

    def _pwquality_options_for_user(self, user):
        entries = self._pam_password_module_entries("passwd")
        if not entries:
            return None

        grouped = {}
        for path, options in entries:
            grouped.setdefault(path, []).append(options)

        result = []
        for path, options_list in grouped.items():
            try:
                text = path.read_text(encoding="utf-8")
            except (OSError, UnicodeError):
                raise RuntimeError(self.tr("Unable to verify the password against the active password policy."))

            if ("# ALT Center group password policies begin" in text or
                    "# ALT Center group password policies end" in text):
                selected = self._pwquality_group_options(text, user)
                if selected is None:
                    raise RuntimeError(self.tr("Unable to verify the password against the active password policy."))
                result.append(selected)
            else:
                result.extend(options_list)

        return result or None

    def _load_pwquality_library(self):
        names = []
        found = ctypes.util.find_library("pwquality")
        if found:
            names.append(found)
        names.extend(("libpwquality.so.1", "libpwquality.so"))

        library = None
        for name in dict.fromkeys(names):
            try:
                library = ctypes.CDLL(name)
                break
            except OSError:
                continue
        if library is None:
            raise RuntimeError(self.tr("Unable to verify the password against the active password policy."))

        try:
            library.pwquality_default_settings.restype = ctypes.c_void_p
            library.pwquality_free_settings.argtypes = [ctypes.c_void_p]
            library.pwquality_read_config.argtypes = [ctypes.c_void_p, ctypes.c_char_p, ctypes.c_void_p]
            library.pwquality_read_config.restype = ctypes.c_int
            library.pwquality_set_option.argtypes = [ctypes.c_void_p, ctypes.c_char_p]
            library.pwquality_set_option.restype = ctypes.c_int
            library.pwquality_check.argtypes = [
                ctypes.c_void_p, ctypes.c_char_p, ctypes.c_char_p, ctypes.c_char_p, ctypes.c_void_p
            ]
            library.pwquality_check.restype = ctypes.c_int
            library.pwquality_generate.argtypes = [ctypes.c_void_p, ctypes.c_int, ctypes.POINTER(ctypes.c_void_p)]
            library.pwquality_generate.restype = ctypes.c_int
            library.pwquality_get_int_value.argtypes = [
                ctypes.c_void_p, ctypes.c_int, ctypes.POINTER(ctypes.c_int)
            ]
            library.pwquality_get_int_value.restype = ctypes.c_int
        except AttributeError:
            raise RuntimeError(self.tr("Unable to verify the password against the active password policy."))

        return library

    def _new_pwquality_settings(self, library, module_options):
        settings = library.pwquality_default_settings()
        if not settings:
            raise RuntimeError(self.tr("Unable to verify the password against the active password policy."))

        try:
            config_path = None
            for option in module_options:
                if option.startswith("conf="):
                    config_path = option.split("=", 1)[1]
            if config_path == "":
                raise RuntimeError(self.tr("Unable to verify the password against the active password policy."))

            config_arg = os.fsencode(config_path) if config_path is not None else None
            if library.pwquality_read_config(settings, config_arg, None) != 0:
                raise RuntimeError(self.tr("Unable to verify the password against the active password policy."))

            for option in module_options:
                if (option == "debug" or option == "reject_username" or
                        option.startswith("conf=") or option.startswith("type=") or
                        option.startswith("authtok_type=") or option.startswith("difignore=") or
                        option in ("use_authtok", "use_first_pass", "try_first_pass")):
                    continue
                if library.pwquality_set_option(settings, option.encode("utf-8")) < 0:
                    raise RuntimeError(self.tr("Unable to verify the password against the active password policy."))

            return settings
        except Exception:
            library.pwquality_free_settings(settings)
            raise

    def _pwquality_contexts(self, users):
        user_options = []
        for user in users:
            options = self._pwquality_options_for_user(user)
            if options is None:
                return None
            user_options.append((user, options))

        library = self._load_pwquality_library()
        contexts = []
        try:
            for user, option_sets in user_options:
                for options in option_sets:
                    settings = self._new_pwquality_settings(library, options)
                    contexts.append((user, settings))
        except Exception:
            for user, settings in contexts:
                library.pwquality_free_settings(settings)
            raise

        return library, contexts

    def _free_pwquality_contexts(self, library, contexts):
        for user, settings in contexts:
            library.pwquality_free_settings(settings)

    def _check_pwquality_password(self, library, settings, password, user):
        if "\n" in password or "\r" in password or "\0" in password:
            return False
        result = library.pwquality_check(
            settings,
            password.encode("utf-8"),
            None,
            user.encode("utf-8"),
            None
        )
        if result >= 0:
            return True
        if -30 <= result <= -9:
            return False
        return None

    def _pwquality_enforces_for_root(self, library, settings):
        enforcing = ctypes.c_int()
        enforce_for_root = ctypes.c_int()
        if library.pwquality_get_int_value(settings, 17, ctypes.byref(enforcing)) != 0:
            raise RuntimeError(self.tr("Unable to verify the password against the active password policy."))
        if library.pwquality_get_int_value(settings, 19, ctypes.byref(enforce_for_root)) != 0:
            raise RuntimeError(self.tr("Unable to verify the password against the active password policy."))
        return enforcing.value != 0 and enforce_for_root.value != 0

    def _pwquality_generate_one(self, library, settings):
        password_pointer = ctypes.c_void_p()
        result = library.pwquality_generate(settings, 96, ctypes.byref(password_pointer))
        if result < 0 or not password_pointer.value:
            if password_pointer.value:
                libc = ctypes.CDLL(None)
                libc.free.argtypes = [ctypes.c_void_p]
                libc.free.restype = None
                libc.free(password_pointer)
            return None

        libc = ctypes.CDLL(None)
        libc.free.argtypes = [ctypes.c_void_p]
        libc.free.restype = None
        try:
            password = ctypes.string_at(password_pointer.value).decode("utf-8")
        except UnicodeError:
            return None
        finally:
            libc.free(password_pointer)

        if not password or any(char in password for char in (":", "\n", "\r", "\0")):
            return None
        return password

    def _random_pwquality_password(self, library, contexts):
        for _ in range(100):
            for _, generator_settings in contexts:
                password = self._pwquality_generate_one(library, generator_settings)
                if password is None:
                    continue

                valid = True
                for user, settings in contexts:
                    result = self._check_pwquality_password(library, settings, password, user)
                    if result is None:
                        raise RuntimeError(self.tr("Unable to verify the password against the active password policy."))
                    if not result:
                        valid = False
                        break
                if valid:
                    return password

        raise RuntimeError(self.tr("Unable to generate a password that meets the active policy."))

    def _random_password_12(self) -> str:
        alphabet = string.ascii_letters + string.digits
        return "".join(secrets.choice(alphabet) for _ in range(12))

    def _random_passwdqc_password(self, users):
        min_n1, max_length = self._read_passwdqc_config()
        length = min(max_length, max(12, min_n1))
        lower = string.ascii_lowercase
        upper = string.ascii_uppercase
        alphabet = lower + upper
        randomizer = secrets.SystemRandom()

        for _ in range(100):
            tail = [secrets.choice(upper)]
            tail.extend(secrets.choice(alphabet) for _ in range(length - 2))
            randomizer.shuffle(tail)
            password = secrets.choice(lower) + "".join(tail)
            valid = True
            for user in users:
                result = self._check_passwdqc_password(password, user)
                if result is None:
                    raise RuntimeError(self.tr("Unable to verify the password against the active password policy."))
                if not result:
                    valid = False
                    break
            if valid:
                return password

        raise RuntimeError(self.tr("Unable to generate a password that meets the active policy."))

    def _on_generate(self) -> None:
        try:
            users = self._selected_users()
            if not users:
                return

            mode = self._passwdqc_enforce_mode()
            if mode is not None:
                password = self._random_passwdqc_password(users)
            else:
                contexts = self._pwquality_contexts(users)
                if contexts is not None:
                    library, settings = contexts
                    try:
                        password = self._random_pwquality_password(library, settings)
                    finally:
                        self._free_pwquality_contexts(library, settings)
                else:
                    password = self._random_password_12()

            self.ed_new.setText(password)
            self.ed_new.selectAll()
            self.ed_new.setFocus()
        except Exception as e:
            QMessageBox.warning(self, self.tr("Password policy"), str(e))

    def _on_copy(self) -> None:
        pwd = self.ed_new.text()
        if not pwd:
            return
        try:
            QApplication.clipboard().setText(pwd)
        except Exception:
            pass

    def _on_toggle_show(self) -> None:
        if self.ed_new.echoMode() == QLineEdit.EchoMode.Password:
            self.ed_new.setEchoMode(QLineEdit.EchoMode.Normal)
            self.btn_show.setText(self.tr("Hide"))
        else:
            self.ed_new.setEchoMode(QLineEdit.EchoMode.Password)
            self.btn_show.setText(self.tr("Show"))

    def _on_change_password(self) -> None:
        users = self._selected_users()

        if not users:
            return

        allowed_users = {name for name, uid in get_local_users()}
        if any(user not in allowed_users for user in users):
            QMessageBox.critical(self, self.tr("Error"), self.tr("Failed to set password."))
            return

        pwd = self.ed_new.text()

        if not pwd:
            return

        try:
            mode = self._passwdqc_enforce_mode()
            if mode == "everyone":
                for user in users:
                    result = self._check_passwdqc_password(pwd, user)
                    if result is False:
                        QMessageBox.warning(
                            self,
                            self.tr("Password policy"),
                            self.tr("Password does not meet password policy requirements.")
                        )
                        return
                    if result is None:
                        QMessageBox.critical(
                            self,
                            self.tr("Error"),
                            self.tr("Unable to verify the password against the active password policy.")
                        )
                        return

            contexts = self._pwquality_contexts(users)
            if contexts is not None:
                library, settings = contexts
                try:
                    for user, quality_settings in settings:
                        if not self._pwquality_enforces_for_root(library, quality_settings):
                            continue
                        result = self._check_pwquality_password(library, quality_settings, pwd, user)
                        if result is False:
                            QMessageBox.warning(
                                self,
                                self.tr("Password policy"),
                                self.tr("Password does not meet password policy requirements.")
                            )
                            return
                        if result is None:
                            QMessageBox.critical(
                                self,
                                self.tr("Error"),
                                self.tr("Unable to verify the password against the active password policy.")
                            )
                            return
                finally:
                    self._free_pwquality_contexts(library, settings)

            data = "".join(f"{u}:{pwd}\n" for u in users).encode("utf-8")

            chpasswd = "/usr/sbin/chpasswd"

            if self._is_root():
                cmd = [chpasswd]
            else:
                cmd = ["pkexec", chpasswd]

            p = subprocess.run(cmd, input=data, stdout=subprocess.PIPE, stderr=subprocess.PIPE, check=False)

            if p.returncode != 0:
                err = (p.stderr or b"").decode("utf-8", errors="ignore").strip()
                QMessageBox.critical(self, self.tr("Error"), err or self.tr("Failed to set password."))
                return

            QMessageBox.information(self, self.tr("Done"), self.tr("The password has been changed"))
        except Exception as e:
            QMessageBox.critical(self, self.tr("Error"), str(e))


class ChangePasswordPlugin(plugins.Base):
    requires_admin = True

    def __init__(self, plist=None, pane: QStackedWidget = None):
        super().__init__("change_password", 160, plist, pane)
        if self.plist is not None and self.pane is not None:
            self.node = QStandardItem(self.tr("Change password"))
            self.node.setData(self.name)
            self.add_to_menu(self.node)
            self.pane.addWidget(QWidget())

    def _do_start(self, idx: int):
        main_palette = self.pane.window().palette()
        self.pane.insertWidget(idx, ChangePassword(main_palette))