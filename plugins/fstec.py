#!/usr/bin/python3

import plugins
import json

from PyQt6.QtWidgets import QWidget, QVBoxLayout, QStackedWidget, QLabel, QTreeWidget, QTreeWidgetItem, QAbstractItemView, QPlainTextEdit, QHeaderView
from PyQt6.QtGui import QStandardItem, QStandardItemModel, QColor, QBrush
from PyQt6.QtCore import Qt


class FSTECWidget(QWidget):
    def __init__(self, main_window = None):
        super().__init__()

        self.main_window = main_window

        self.status_label = None
        self.tree = None
        self.details = None

        self.initUI()
        self.loadSavedResults()

    def initUI(self):
        layout = QVBoxLayout()
        layout.setContentsMargins(10, 10, 10, 10)

        self.status_label = QLabel("")
        self.status_label.setTextInteractionFlags(Qt.TextInteractionFlag.TextSelectableByMouse)
        self.status_label.setVisible(False)
        layout.addWidget(self.status_label)

        self.tree = QTreeWidget()
        self.tree.setColumnCount(2)
        self.tree.setHeaderLabels([
            self.tr("Option"),
            self.tr("Check result")
        ])
        self.tree.header().setSectionResizeMode(0, QHeaderView.ResizeMode.Interactive)
        self.tree.header().setSectionResizeMode(1, QHeaderView.ResizeMode.Interactive)
        self.tree.header().setStretchLastSection(False)
        self.tree.header().setSectionsMovable(True)
        self.tree.header().setMinimumSectionSize(80)
        self.tree.setAlternatingRowColors(True)
        self.tree.setSelectionBehavior(QAbstractItemView.SelectionBehavior.SelectRows)
        self.tree.setEditTriggers(QAbstractItemView.EditTrigger.NoEditTriggers)
        self.tree.itemSelectionChanged.connect(self.onSelectionChanged)

        layout.addWidget(self.tree, 1)

        self.details = QPlainTextEdit()
        self.details.setReadOnly(True)
        self.details.setMinimumHeight(70)
        self.details.setMaximumHeight(105)
        self.details.setVerticalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAsNeeded)
        self.details.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAsNeeded)
        self.details.setLineWrapMode(QPlainTextEdit.LineWrapMode.NoWrap)
        self.details.setPlainText("")
        layout.addWidget(self.details)

        self.setLayout(layout)

    def sanitize_str(self, input_str):
        return "" if input_str is None else str(input_str)

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

    def groupDisplayName(self, name):
        if name == "boot":
            return self.tr("Boot Option")

        if name == "sysctl":
            return self.tr("Sysctl Option")

        if name == "kernel":
            return self.tr("Kernel Option")

        return name

    def resultBrush(self, value):
        text = self.sanitize_str(value)

        if text == "OK":
            return QBrush(QColor("#2e7d32"))

        if text == "FAIL":
            return QBrush(QColor("#c62828"))

        if text == "unknown":
            return QBrush(QColor("#ef6c00"))

        return QBrush(QColor("#616161"))

    def makeGroupItem(self, title):
        item = QTreeWidgetItem([title, ""])
        font = item.font(0)
        font.setBold(True)
        item.setFont(0, font)
        item.setFont(1, font)
        item.setData(0, Qt.ItemDataRole.UserRole, None)
        return item

    def makeResultItem(self, row):
        option = self.sanitize_str(row[0]) if len(row) > 0 else ""
        current = self.sanitize_str(row[1]) if len(row) > 1 else ""
        recommended = self.sanitize_str(row[2]) if len(row) > 2 else ""
        result = self.sanitize_str(row[3]) if len(row) > 3 else ""
        alternative = self.sanitize_str(row[4]) if len(row) > 4 else ""

        item = QTreeWidgetItem([
            self.displayValue(option),
            self.displayValue(result)
        ])

        item.setForeground(1, self.resultBrush(result))
        item.setData(0, Qt.ItemDataRole.UserRole, {
            "option": option,
            "current": current,
            "recommended": recommended,
            "result": result,
            "alternative": alternative
        })

        return item

    def addGroup(self, name, rows):
        group_item = self.makeGroupItem(self.groupDisplayName(name))
        self.tree.addTopLevelItem(group_item)

        for row in rows:
            group_item.addChild(self.makeResultItem(row))

        group_item.setExpanded(True)

    def clearTree(self):
        self.tree.clear()
        self.details.setPlainText("")

    def loadSavedResults(self):
        path = "/tmp/altcenter_fstec_check.json"

        try:
            with open(path, "r", encoding="utf-8", errors="replace") as f:
                data = json.load(f)
        except:
            self.clearTree()
            self.status_label.setText(self.tr("Saved FSTEC check result not found"))
            self.status_label.setVisible(True)
            return

        self.status_label.setText("")
        self.status_label.setVisible(False)

        self.clearTree()

        self.addGroup("boot", data.get("boot", []))
        self.addGroup("sysctl", data.get("sysctl", []))
        self.addGroup("kernel", data.get("kernel", []))

        self.tree.resizeColumnToContents(0)
        self.tree.resizeColumnToContents(1)

    def onSelectionChanged(self):
        items = self.tree.selectedItems()

        if not items:
            self.details.setPlainText("")
            return

        item = items[0]
        data = item.data(0, Qt.ItemDataRole.UserRole)

        if data is None:
            self.details.setPlainText(item.text(0))
            return

        lines = [
            "%s: %s" % (self.tr("Option"), self.displayValue(data.get("option", ""))),
            "%s: %s" % (self.tr("Current"), self.displayValue(data.get("current", ""))),
            "%s: %s" % (self.tr("Recommended value"), self.displayValue(data.get("recommended", ""))),
            "%s: %s" % (self.tr("Check result"), self.displayValue(data.get("result", ""))),
            "%s: %s" % (self.tr("Alternative"), self.displayValue(data.get("alternative", "")))
        ]

        self.details.setPlainText("\n".join(lines))

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