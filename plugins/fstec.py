#!/usr/bin/python3

import plugins
import json

from PyQt6.QtWidgets import QWidget, QVBoxLayout, QHBoxLayout, QStackedWidget, QLabel, QTableWidget, QTableWidgetItem, QHeaderView, QTabWidget, QAbstractItemView
from PyQt6.QtGui import QStandardItem, QStandardItemModel
from PyQt6.QtCore import Qt


class FSTECWidget(QWidget):
    def __init__(self, main_window = None):
        super().__init__()

        self.main_window = main_window

        self.status_label = None
        self.tabs = None
        self.boot_table = None
        self.sysctl_table = None
        self.kernel_table = None

        self.initUI()
        self.loadSavedResults()

    def initUI(self):
        layout = QVBoxLayout()
        layout.setContentsMargins(10, 10, 10, 10)

        self.status_label = QLabel("")
        self.status_label.setTextInteractionFlags(Qt.TextInteractionFlag.TextSelectableByMouse)
        self.status_label.setVisible(False)
        layout.addWidget(self.status_label)

        self.tabs = QTabWidget()

        self.boot_table = self.createTable()
        self.sysctl_table = self.createTable()
        self.kernel_table = self.createTable()

        self.tabs.addTab(self.boot_table, self.tr("Boot Option"))
        self.tabs.addTab(self.sysctl_table, self.tr("Sysctl Option"))
        self.tabs.addTab(self.kernel_table, self.tr("Kernel Option"))

        layout.addWidget(self.tabs, 1)

        self.setLayout(layout)

    def displayValue(self, value):
        text = self.sanitize_str(value)

        if text == "unknown":
            return self.tr("unknown")

        if text == "not present":
            return self.tr("not present")

        if text == "no value":
            return self.tr("no value")

        if text == "None":
            return self.tr("None")

        if text == "is not set":
            return self.tr("is not set")

        if text == "config not found":
            return self.tr("config not found")

        return text

    def createTable(self):
        table = QTableWidget()
        table.setColumnCount(5)
        table.setHorizontalHeaderLabels([
            self.tr("Option"),
            self.tr("Current"),
            self.tr("Recommended value"),
            self.tr("Check result"),
            self.tr("Alternative")
        ])

        table.horizontalHeader().setSectionResizeMode(0, QHeaderView.ResizeMode.Interactive)
        table.horizontalHeader().setSectionResizeMode(1, QHeaderView.ResizeMode.Interactive)
        table.horizontalHeader().setSectionResizeMode(2, QHeaderView.ResizeMode.Interactive)
        table.horizontalHeader().setSectionResizeMode(3, QHeaderView.ResizeMode.Interactive)
        table.horizontalHeader().setSectionResizeMode(4, QHeaderView.ResizeMode.Interactive)
        table.horizontalHeader().setStretchLastSection(False)
        table.horizontalHeader().setSectionsMovable(True)

        table.verticalHeader().setVisible(False)

        table.setEditTriggers(QAbstractItemView.EditTrigger.NoEditTriggers)
        table.setSelectionBehavior(QAbstractItemView.SelectionBehavior.SelectRows)
        table.setAlternatingRowColors(True)
        table.setWordWrap(False)

        return table

    def sanitize_str(self, input_str):
        return "" if input_str is None else str(input_str)

    def setTableRows(self, table, rows):
        table.setRowCount(len(rows))

        for row_index, row in enumerate(rows):
            for column_index, value in enumerate(row):
                item = QTableWidgetItem(self.displayValue(value))
                item.setTextAlignment(Qt.AlignmentFlag.AlignVCenter | Qt.AlignmentFlag.AlignLeft)
                table.setItem(row_index, column_index, item)

        table.resizeColumnsToContents()
        table.setColumnWidth(4, table.columnWidth(4) + 40)
        table.resizeRowsToContents()

    def clearTables(self):
        self.boot_table.setRowCount(0)
        self.sysctl_table.setRowCount(0)
        self.kernel_table.setRowCount(0)

    def loadSavedResults(self):
        path = "/tmp/altcenter_fstec_check.json"

        try:
            with open(path, "r", encoding="utf-8", errors="replace") as f:
                data = json.load(f)
        except:
            self.clearTables()
            self.status_label.setText(self.tr("Saved FSTEC check result not found"))
            self.status_label.setVisible(True)
            return

        self.setTableRows(self.boot_table, data.get("boot", []))
        self.setTableRows(self.sysctl_table, data.get("sysctl", []))
        self.setTableRows(self.kernel_table, data.get("kernel", []))

        warning = data.get("warning", "")

        if warning:
            self.status_label.setText(self.tr(warning))
            self.status_label.setVisible(True)
        else:
            self.status_label.setText("")
            self.status_label.setVisible(False)

class PluginFSTEC(plugins.Base):
    requires_admin = True

    def __init__(self, plist: QStandardItemModel = None, pane: QStackedWidget = None):
        super().__init__("fstec", 130, plist, pane)

        if self.plist != None and self.pane != None:
            self.node = QStandardItem(self.tr("FSTEC recommendations"))
            self.node.setData(self.name)
            self.plist.appendRow([self.node])
            self.pane.addWidget(QWidget())

    def _do_start(self, idx: int):
        main_window = self.pane.window()
        main_widget = FSTECWidget(main_window)
        self.pane.insertWidget(idx, main_widget)