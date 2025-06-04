#!/usr/bin/python3

import plugins
from PyQt5.QtWidgets import (
    QWidget, QVBoxLayout, QPushButton, QMessageBox,
    QListWidget, QListWidgetItem, QTextEdit, QSplitter
)
from PyQt5.QtGui import QStandardItem, QFont, QColor
from PyQt5.QtCore import Qt, QProcess
import my_utils
import dbus
import os

class Components(plugins.Base):
    def __init__(self):
        super().__init__("components", 90)
        self.node = None
        self.list_widget = None
        self.console = None
        self.info_panel = None
        self.btn_install = None
        self.proc_install = None

        self.operation_in_progress = False

        self.components_info = []  # name, key, packages, installed

        self.translations = {
            "education-preschool": self.tr("Preschool education"),
            "education-highschool": self.tr("High school education"),
            "education-secondary-vocational": self.tr("Secondary vocational education"),
            "education-university": self.tr("University education"),
            "education-teacher": self.tr("For teachers"),
            "education-server-apps": self.tr("Server applications for education"),
            "education-robotics": self.tr("Robotics in education"),
            "moodle": self.tr("Moodle"),
            "nextcloud": self.tr("Nextcloud"),
            "mediawiki": self.tr("MediaWiki"),
            "yandex-browser-stable": self.tr("Yandex Browser"),
            "fonts-ttf-ms": self.tr("Microsoft TTF Fonts"),
        }

    def start(self, plist, pane):
        self.main_window = pane.window()

        self.node = QStandardItem(self.tr("Components"))
        self.node.setData(self.getName())
        plist.appendRow([self.node])

        main_widget = QWidget()
        main_layout = QVBoxLayout(main_widget)
        main_layout.setContentsMargins(5, 5, 5, 5)

        splitter = QSplitter(Qt.Horizontal)

        self.list_widget = QListWidget()
        self.list_widget.itemChanged.connect(self.update_install_button_state)
        self.list_widget.itemClicked.connect(self.show_item_info)
        splitter.addWidget(self.list_widget)

        self.info_panel = QTextEdit()
        self.info_panel.setReadOnly(True)
        self.info_panel.setFont(QFont("Sans", 10))
        self.info_panel.setMinimumWidth(200)
        self.info_panel.setVisible(False)
        splitter.addWidget(self.info_panel)

        splitter.setStretchFactor(0, 3)
        splitter.setStretchFactor(1, 2)

        main_layout.addWidget(splitter, 1)

        self.console = QTextEdit()
        self.console.setReadOnly(True)
        self.console.setVisible(False)
        self.console.setFont(QFont("Courier", 10))
        main_layout.addWidget(self.console)

        self.btn_install = QPushButton(self.tr("Apply"))
        self.btn_install.setEnabled(False)
        self.btn_install.clicked.connect(self.start_installation)
        self.btn_install.setMinimumHeight(30)
        main_layout.addWidget(self.btn_install)

        self.load_components_from_dbus()
        self.populate_list()

        self.proc_install = QProcess(self)
        self.proc_install.readyReadStandardOutput.connect(self.on_install_output)
        self.proc_install.readyReadStandardError.connect(self.on_install_error)
        self.proc_install.finished.connect(self.on_install_finished)

        self.index = pane.addWidget(main_widget)


    def load_components_from_dbus(self):
        self.components_info.clear()

        base_dir = os.path.dirname(os.path.abspath(__file__))
        list_path = os.path.join(base_dir, "..", "res", "list_components.txt")

        pkg_order = []
        try:
            with open(list_path, "r", encoding="utf-8") as f:
                for line in f:
                    line = line.strip()
                    if line:
                        pkg_order.append(line)
        except Exception as e:
            QMessageBox.critical(None, self.tr("Error"), self.tr("Failed to read list_components.txt:") + f"\n{e}")
            return

        try:
            bus = dbus.SystemBus()
            proxy = bus.get_object('org.altlinux.alterator', '/org/altlinux/alterator/global')
            iface = dbus.Interface(proxy, 'org.altlinux.alterator.batch_components1')
            raw_data, _ = iface.Info()

            text = bytes(raw_data).replace(b'\x00', b'').decode("utf-8")
            blocks = text.strip().split("\n\n")
        except Exception as e:
            QMessageBox.critical(None, self.tr("Error"), self.tr("Failed to get data via D-Bus:") + f"\n{e}")
            return

        for key in pkg_order:
            display_name = self.translations.get(key, key)
            packages = []

            for block in blocks:
                lines = block.strip().splitlines()
                found_name = None
                found_packages = []
                in_packages = False

                for line in lines:
                    line = line.strip()
                    if not line:
                        continue

                    if line.startswith("name ="):
                        found_name = line.split("=", 1)[1].strip().strip('"')

                    elif line.startswith("[packages]"):
                        in_packages = True
                        continue

                    elif in_packages:
                        if line.startswith("[") or "=" not in line:
                            in_packages = False
                            continue

                        pkg, val = map(str.strip, line.split("=", 1))
                        if val == "{}" and pkg and "\x00" not in pkg and pkg != "type":
                            found_packages.append(pkg)

                if found_name == key:
                    packages = found_packages
                    break

            if packages:
                installed = all(my_utils.check_package_installed(pkg) for pkg in packages)
            else:
                installed = my_utils.check_package_installed(key)

            self.components_info.append({
                "name": display_name,
                "key": key,
                "packages": packages,
                "installed": installed
            })


    def populate_list(self):
        self.list_widget.clear()
        for comp in self.components_info:
            item = QListWidgetItem(comp["name"])
            item.setFlags(item.flags() | Qt.ItemIsUserCheckable | Qt.ItemIsEnabled)
            if comp["installed"]:
                item.setCheckState(Qt.Checked)
            else:
                item.setCheckState(Qt.Unchecked)
            self.list_widget.addItem(item)


    def update_install_button_state(self):
        if self.operation_in_progress:
            self.btn_install.setEnabled(False)
            return

        enable = False

        for i in range(self.list_widget.count()):
            item = self.list_widget.item(i)
            if not item.flags() & Qt.ItemIsUserCheckable:
                continue

            name = item.text()
            checked = item.checkState() == Qt.Checked

            for comp in self.components_info:
                if comp["name"] == name:
                    if (not comp["installed"] and checked) or (comp["installed"] and not checked):
                        enable = True
                    break

            if enable:
                break

        self.btn_install.setEnabled(enable)


    def get_selected_packages(self):
        selected = []
        for i in range(self.list_widget.count()):
            item = self.list_widget.item(i)
            if item.flags() & Qt.ItemIsUserCheckable and item.checkState() == Qt.Checked:
                name = item.text()
                for comp in self.components_info:
                    if comp["name"] == name and not comp["installed"]:
                        if comp["packages"]:
                            selected.extend(pkg for pkg in comp["packages"]
                                            if not my_utils.check_package_installed(pkg))
                        else:
                            selected.append(comp["key"])
        return selected


    def get_packages_to_remove(self):
        components_to_remove = []
        for i in range(self.list_widget.count()):
            item = self.list_widget.item(i)
            if item.flags() & Qt.ItemIsUserCheckable and item.checkState() == Qt.Unchecked:
                name = item.text()
                for comp in self.components_info:
                    if comp["name"] == name and comp["installed"]:
                        components_to_remove.append(comp)

        if not components_to_remove:
            return []

        used_elsewhere = set()
        for comp in self.components_info:
            if comp not in components_to_remove and comp["installed"]:
                used_elsewhere.update(comp["packages"])

        to_remove = set()
        for comp in components_to_remove:
            if not comp["packages"]:
                to_remove.add(comp["key"])
            else:
                for pkg in comp["packages"]:
                    if pkg not in used_elsewhere:
                        to_remove.add(pkg)

        return list(to_remove)


    def start_installation(self):
        self.operation_in_progress = True
        self.btn_install.setEnabled(False)

        if hasattr(self.main_window, "block_close"):
            self.main_window.block_close = True

        install_packages = self.get_selected_packages()
        remove_packages = self.get_packages_to_remove()

        if not install_packages and not remove_packages:
            QMessageBox.information(None, self.tr("No changes"), self.tr("You did not select any components for installation or removal."))
            return

        if not self.console.isVisible():
            self.console.setVisible(True)

        if install_packages:
            cmd = ["pkexec", "apt-get", "install", "-y"] + install_packages
            self.proc_install.start(" ".join(cmd))
        elif remove_packages:
            cmd = ["pkexec", "rpm", "-e"] + remove_packages
            self.proc_install.start(" ".join(cmd))


    def append_to_console(self, text, is_error=False):
        cursor = self.console.textCursor()
        cursor.movePosition(cursor.End)
        fmt = cursor.charFormat()
        fmt.setForeground(QColor("red") if is_error else QColor("black"))
        cursor.setCharFormat(fmt)
        cursor.insertText(text)
        self.console.setTextCursor(cursor)
        self.console.ensureCursorVisible()


    def refresh_installed_status(self):
        self.load_components_from_dbus()
        self.populate_list()


    def on_install_finished(self, exit_code, exit_status):
        self.operation_in_progress = False
        self.refresh_installed_status()
        self.update_install_button_state()

        if exit_code == 0:
            QMessageBox.information(None, self.tr("Success"), self.tr("Installation completed successfully!"))
        else:
            QMessageBox.critical(None, self.tr("Error"), self.tr("Installation failed."))

        self.refresh_installed_status()
        if hasattr(self.main_window, "block_close"):
            self.main_window.block_close = False


    def on_install_output(self):
        output = self.proc_install.readAllStandardOutput().data().decode()
        self.append_to_console(output)


    def on_install_error(self):
        error = self.proc_install.readAllStandardError().data().decode()
        self.append_to_console(error, is_error=True)


    def show_item_info(self, item):
        if not item:
            return

        name = item.text()
        for comp in self.components_info:
            if comp["name"] == name:
                lines = []
                lines.append(self.tr("Component name: ") + name)
                lines.append("")

                if comp["packages"]:
                    lines.append(self.tr("This component consists of:"))
                    for pkg in comp["packages"]:
                        lines.append(f"  - {pkg}")
                else:
                    lines.append(self.tr("This component: ") + comp["key"])

                self.info_panel.setText("\n".join(lines))
                self.info_panel.setVisible(True)
                return
