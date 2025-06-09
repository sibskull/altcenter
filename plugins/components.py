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
import alterator

list_path = "/etc/altcenter/list-components"

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

        self.components_info = [] # List of components
        self.component_map = {}

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
        self.list_widget.itemClicked.connect(self.show_item_info)
        splitter.addWidget(self.list_widget)

        self.info_panel = QTextEdit()
        self.info_panel.setReadOnly(True)
        self.info_panel.setMinimumWidth(200)
        self.info_panel.setVisible(False)
        splitter.addWidget(self.info_panel)

        splitter.setStretchFactor(0, 3)
        splitter.setStretchFactor(1, 2)

        main_layout.addWidget(splitter, 1)

        self.console = QTextEdit()
        self.console.setReadOnly(True)
        self.console.setVisible(False)
        self.console.setFont(QFont("Monospace", 10))
        main_layout.addWidget(self.console)

        self.btn_install = QPushButton(self.tr("Apply"))
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

        # Read ordered list of allowed components
        components_order = []
        try:
            with open(list_path, "r") as f:
                components_order = list(filter(lambda x: x and not x.startswith("#"), [line.strip() for line in f]))
        except:
            pass

        # Read all components by D-Bus
        clist = alterator.Components().fetch()
        self.component_map = {c.name:c for c in clist}
        for name in components_order:
            i = self.component_map.get(name, None)
            if i:
                self.components_info.append(i)

    def populate_list(self):
        self.list_widget.clear()
        for comp in self.components_info:
            item = QListWidgetItem(comp.display_name)
            item.setFlags(item.flags() | Qt.ItemIsUserCheckable | Qt.ItemIsEnabled)
            item.setData(1, comp.name)
            if comp.installed:
                item.setCheckState(Qt.Checked)
            else:
                item.setCheckState(Qt.Unchecked)
            self.list_widget.addItem(item)


    def get_components_to_install(self):
        selected = []
        for i in range(self.list_widget.count()):
            item = self.list_widget.item(i)
            if item.flags() & Qt.ItemIsUserCheckable and item.checkState() == Qt.Checked:
                comp = self.component_map.get(item.data(1), None)
                if comp and not comp._installed:
                    selected.append(comp)
        return selected


    def get_components_to_remove(self):
        components_to_remove = []
        for i in range(self.list_widget.count()):
            item = self.list_widget.item(i)
            if item.flags() & Qt.ItemIsUserCheckable and item.checkState() == Qt.Unchecked:
                comp = self.component_map.get(item.data(1), None)
                if comp and comp._installed:
                    components_to_remove.append(comp)

        return components_to_remove


    def start_installation(self):
        self.operation_in_progress = True

        #if hasattr(self.main_window, "block_close"):
        #    self.main_window.block_close = True

        install_components = self.get_components_to_install()
        remove_components = self.get_components_to_remove()

        if not install_components and not remove_components:
            # self.append_to_console(self.tr("You did not select any components for installation or removal."))
            return

        # TODO need smart deploy components. Now only package installation is supported.
        install_packages = []
        for comp in install_components:
            install_packages.extend(comp.packages)
        remove_packages = []
        for comp in remove_components:
            remove_packages.extend(comp.packages)

        if not self.console.isVisible():
            self.console.setVisible(True)

        #print("install_components: ", install_components)
        #print("remove_components: ", remove_components)
        #print("install_packages: ", install_packages)
        #print("remove_packages: ", remove_packages)

        # TODO: need use D-Bus Alterator call
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

        if exit_code == 0:
            QMessageBox.information(None, self.tr("Success"), self.tr("Installation completed successfully!"))
        else:
            QMessageBox.critical(None, self.tr("Error"), self.tr("Installation failed."))

        self.refresh_installed_status()
        #if hasattr(self.main_window, "block_close"):
        #    self.main_window.block_close = False


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
            if comp.name == name:
                lines = []
                lines.append(comp.comment)
                lines.append("")

                if comp.packages:
                    lines.append(self.tr("This component consists of:"))
                    for pkg in comp.packages:
                        lines.append(f"  - {pkg}")
                else:
                    lines.append(self.tr("This component: ") + comp["key"])

                self.info_panel.setText("\n".join(lines))
                self.info_panel.setVisible(True)
                return
