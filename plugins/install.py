#!/usr/bin/python3

import plugins
from PyQt5.QtWidgets import (
    QWidget, QVBoxLayout, QPushButton, QMessageBox,
    QListWidget, QListWidgetItem, QHBoxLayout, QTextEdit
)
from PyQt5.QtGui import QStandardItem, QFont, QColor
from PyQt5.QtCore import Qt, QProcess
import my_utils

class AppInstall(plugins.Base):
    def __init__(self):
        super().__init__("install", 80)
        self.node = None
        self.list_widget = None
        self.console = None
        self.pkg_mapping = {
            "Hw-probe": "hw-probe",
            "Yandex": "yandex-browser-stable",
            "Шрифты от Microsoft": "fonts-ttf-ms"
        }

        self.num_packages = 1
        self.current_package = 0

    def start(self, plist, pane):
        self.main_window = pane.window()

        self.node = QStandardItem(self.tr("App Install"))
        self.node.setData(self.getName())
        plist.appendRow([self.node])

        main_widget = QWidget()
        layout = QVBoxLayout(main_widget)
        layout.setContentsMargins(5, 5, 5, 5)
        layout.setSpacing(10)

        self.list_widget = QListWidget()
        self.list_widget.itemChanged.connect(self.update_install_button_state)
        layout.addWidget(self.list_widget, 1)

        for app, pkg in self.pkg_mapping.items():
            item = QListWidgetItem(app)
            if my_utils.check_package_installed(pkg):
                item.setCheckState(Qt.Checked)
                item.setFlags(item.flags() & ~Qt.ItemIsUserCheckable & ~Qt.ItemIsEnabled)
            else:
                item.setFlags(item.flags() | Qt.ItemIsUserCheckable)
                item.setCheckState(Qt.Unchecked)
            self.list_widget.addItem(item)

        # Консоль
        self.console = QTextEdit()
        self.console.setReadOnly(True)
        self.console.setVisible(False)
        self.console.setFont(QFont("Courier", 10))
        layout.addWidget(self.console)

        # Кнопки
        button_layout = QHBoxLayout()
        button_layout.setSpacing(10)

        self.btn_update = QPushButton(self.tr("Update System"))
        self.btn_update.clicked.connect(self.start_system_update)
        button_layout.addWidget(self.btn_update)

        self.btn_install = QPushButton(self.tr("Install Selected"))
        self.btn_install.setEnabled(False)
        self.btn_install.clicked.connect(self.start_installation)
        button_layout.addWidget(self.btn_install)

        layout.addLayout(button_layout)

        self.proc_install = QProcess(self)
        self.proc_install.readyReadStandardOutput.connect(self.on_install_output)
        self.proc_install.readyReadStandardError.connect(self.on_install_error)
        self.proc_install.finished.connect(self.on_install_finished)

        self.index = pane.addWidget(main_widget)

    def update_install_button_state(self):
        self.btn_install.setEnabled(any(
            self.list_widget.item(i).flags() & Qt.ItemIsUserCheckable and
            self.list_widget.item(i).checkState() == Qt.Checked
            for i in range(self.list_widget.count())
        ))

    def get_selected_packages(self):
        selected = []
        for i in range(self.list_widget.count()):
            item = self.list_widget.item(i)
            if item.flags() & Qt.ItemIsUserCheckable and item.checkState() == Qt.Checked:
                pkg = self.pkg_mapping.get(item.text())
                if pkg:
                    selected.append(pkg)
        return selected

    def start_installation(self):
        if hasattr(self.main_window, "block_close"):
            self.main_window.block_close = True

        packages = self.get_selected_packages()
        self.num_packages = len(packages)
        if self.num_packages == 0:
            QMessageBox.warning(None, self.tr("Error"), self.tr("No applications selected!"))
            return

        if not self.console.isVisible():
            self.console.setVisible(True)

        self.btn_install.setEnabled(False)
        self.btn_update.setEnabled(False)

        cmd = ["pkexec", "apt-get", "install", "-y"] + packages
        self.proc_install.start(" ".join(cmd))

    def start_system_update(self):
        if hasattr(self.main_window, "block_close"):
            self.main_window.block_close = True

        if not self.console.isVisible():
            self.console.setVisible(True)

        self.btn_install.setEnabled(False)
        self.btn_update.setEnabled(False)
        cmd = 'pkexec sh -c "apt-get update && apt-get dist-upgrade -y"'
        self.proc_install.start(cmd)

    def append_to_console(self, text, is_error=False):
        cursor = self.console.textCursor()
        cursor.movePosition(cursor.End)

        fmt = cursor.charFormat()
        if is_error:
            fmt.setForeground(QColor("red"))
        else:
            fmt.setForeground(QColor("black"))

        cursor.setCharFormat(fmt)
        cursor.insertText(text)
        self.console.setTextCursor(cursor)
        self.console.ensureCursorVisible()

    def refresh_installed_status(self):
        for i in range(self.list_widget.count()):
            item = self.list_widget.item(i)
            pkg = self.pkg_mapping.get(item.text())
            if pkg and my_utils.check_package_installed(pkg):
                item.setCheckState(Qt.Checked)
                item.setFlags(item.flags() & ~Qt.ItemIsUserCheckable & ~Qt.ItemIsEnabled)

    def on_install_finished(self, exit_code, exit_status):
        self.btn_install.setEnabled(True)
        self.btn_update.setEnabled(True)

        if exit_code == 0:
            QMessageBox.information(None, self.tr("Success"), self.tr("Operation completed successfully!"))
        else:
            QMessageBox.critical(None, self.tr("Error"), self.tr("Operation failed. See console for details."))

        self.refresh_installed_status()
        if hasattr(self.main_window, "block_close"):
            self.main_window.block_close = False

    def on_install_output(self):
        output = self.proc_install.readAllStandardOutput().data().decode()
        self.append_to_console(output)

    def on_install_error(self):
        error = self.proc_install.readAllStandardError().data().decode()
        self.append_to_console(error, is_error=True)
