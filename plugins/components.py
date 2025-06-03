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

class Components(plugins.Base):
    def __init__(self):
        super().__init__("components", 90)
        self.node = None
        self.list_widget = None
        self.console = None
        self.info_panel = None
        self.pkg_mapping = {}            # Название → ключ
        self.component_packages = {}     # Ключ → пакеты

        self.num_packages = 1
        self.current_package = 0

    def start(self, plist, pane):
        self.main_window = pane.window()

        self.node = QStandardItem(self.tr("Components"))
        self.node.setData(self.getName())
        plist.appendRow([self.node])

        main_widget = QWidget()
        main_layout = QVBoxLayout(main_widget)
        main_layout.setContentsMargins(5, 5, 5, 5)
        main_layout.setSpacing(10)

        splitter = QSplitter(Qt.Horizontal)

        self.list_widget = QListWidget()
        self.list_widget.itemChanged.connect(self.update_install_button_state)
        self.list_widget.itemClicked.connect(self.show_item_info)
        splitter.addWidget(self.list_widget)

        self.info_panel = QTextEdit()
        self.info_panel.setReadOnly(True)
        self.info_panel.setFont(QFont("Sans", 10))
        self.info_panel.setPlaceholderText("Информация о выбранном компоненте.")
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

        self.btn_install = QPushButton(self.tr("Применить"))
        self.btn_install.setEnabled(False)
        self.btn_install.clicked.connect(self.start_installation)
        self.btn_install.setMinimumHeight(30)
        main_layout.addWidget(self.btn_install)

        # названия ключей из файла
        try:
            with open("/home/sergey/Rabota/Python/altcenter/res/list.txt", "r") as f:
                for line in f:
                    line = line.strip()
                    if not line or ':' not in line:
                        continue
                    name, key = map(str.strip, line.split(':', 1))
                    self.pkg_mapping[name] = key
        except Exception as e:
            QMessageBox.critical(None, "Ошибка", f"Не удалось загрузить список компонентов:\n{e}")
            return

        self.load_component_packages()

        # список
        for name, key in self.pkg_mapping.items():
            item = QListWidgetItem(name)
            if my_utils.check_package_installed(key):
                item.setCheckState(Qt.Checked)
                item.setFlags(item.flags() & ~Qt.ItemIsUserCheckable & ~Qt.ItemIsEnabled)
            else:
                item.setFlags(item.flags() | Qt.ItemIsUserCheckable)
                item.setCheckState(Qt.Unchecked)
            self.list_widget.addItem(item)

        self.proc_install = QProcess(self)
        self.proc_install.readyReadStandardOutput.connect(self.on_install_output)
        self.proc_install.readyReadStandardError.connect(self.on_install_error)
        self.proc_install.finished.connect(self.on_install_finished)

        self.index = pane.addWidget(main_widget)

    def load_component_packages(self):
        wanted = set(self.pkg_mapping.values())
        self.component_packages = {}

        try:
            bus = dbus.SystemBus()
            proxy = bus.get_object('org.altlinux.alterator', '/org/altlinux/alterator/global')
            iface = dbus.Interface(proxy, 'org.altlinux.alterator.batch_components1')

            raw_data, _ = iface.Info()
            text = bytes(raw_data).decode("utf-8")
            blocks = text.strip().split("\n\n")

            for raw_block in blocks:
                lines = raw_block.strip().splitlines()
                name = None
                packages = []
                inside_packages = False

                for line in lines:
                    line = line.strip()

                    if not line:
                        continue

                    if line.startswith("name ="):
                        name = line.split("=", 1)[1].strip().strip('"')

                    elif line.startswith("[packages]"):
                        inside_packages = True

                    elif inside_packages:
                        if "=" in line:
                            pkg = line.split("=")[0].strip()
                            packages.append(pkg)

                if name and name in wanted:
                    self.component_packages[name] = packages

        except Exception as e:
            QMessageBox.critical(None, "Ошибка", f"Ошибка получения данных от alterator:\n{e}")


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
            QMessageBox.warning(None, self.tr("Ошибка"), self.tr("Не выбраны приложения!"))
            return

        if not self.console.isVisible():
            self.console.setVisible(True)

        self.btn_install.setEnabled(False)

        cmd = ["pkexec", "apt-get", "install", "-y"] + packages
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
        for i in range(self.list_widget.count()):
            item = self.list_widget.item(i)
            key = self.pkg_mapping.get(item.text())
            if key and my_utils.check_package_installed(key):
                item.setCheckState(Qt.Checked)
                item.setFlags(item.flags() & ~Qt.ItemIsUserCheckable & ~Qt.ItemIsEnabled)

    def on_install_finished(self, exit_code, exit_status):
        self.btn_install.setEnabled(True)

        if exit_code == 0:
            QMessageBox.information(None, self.tr("Успех"), self.tr("Установка завершена успешно!"))
        else:
            QMessageBox.critical(None, self.tr("Ошибка"), self.tr("Установка завершилась с ошибкой. Смотрите консоль."))

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
        key = self.pkg_mapping.get(name, name)

        lines = []
        lines.append(f"Информация о: {name}")
        lines.append("")

        if key in self.component_packages:
            lines.append("Этот компонент состоит из:")
            for pkg in self.component_packages[key]:
                lines.append(f"  - {pkg}")
        else:
            lines.append("Пакеты не найдены или отсутствуют данные.")

        self.info_panel.setText("\n".join(lines))
        self.info_panel.setVisible(True)
