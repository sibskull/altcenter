#!/usr/bin/python3

import plugins
import os
import json
from PyQt5.QtWidgets import QWidget, QVBoxLayout, QHBoxLayout, QStackedWidget, QListWidget, QListWidgetItem, QTextEdit, QSplitter, QLabel, QPushButton, QLineEdit
from PyQt5.QtGui import QStandardItem, QStandardItemModel, QFont
from PyQt5.QtCore import Qt, QProcess

class PoliciesWindow(QWidget):
    def __init__(self, main_window=None):
        super().__init__()
        self.main_window = main_window
        self._items = []
        self._current_id = None

        self.search = QLineEdit()
        self.search.setPlaceholderText(self.tr("Поиск"))
        self.search.textChanged.connect(self.filterList)

        self.list = QListWidget()
        self.list.itemClicked.connect(self.onItemClicked)

        self.info_title = QLabel()
        self.info_title.setWordWrap(True)
        self.info_title.setAlignment(Qt.AlignLeft | Qt.AlignTop)
        self.info_title.setFont(QFont(self.font().family(), 11, QFont.Bold))

        self.info_text = QTextEdit()
        self.info_text.setReadOnly(True)
        self.info_text.setMinimumHeight(120)
        self.info_text.setMaximumHeight(220)

        self.btn_toggle_console = QPushButton(self.tr("Открыть консоль"))
        self.btn_apply = QPushButton(self.tr("Применить"))
        self.btn_toggle_console.clicked.connect(self.toggleConsole)
        self.btn_apply.clicked.connect(self.applySelected)

        self.log = QTextEdit()
        self.log.setReadOnly(True)
        self.log.setMinimumHeight(140)
        self.log.setVisible(False)

        left = QVBoxLayout()
        left.addWidget(self.search)
        left.addWidget(self.list)

        right = QVBoxLayout()
        right.addWidget(self.info_title)
        right.addWidget(self.info_text)

        left_w = QWidget()
        left_w.setLayout(left)
        right_w = QWidget()
        right_w.setLayout(right)
        right_w.setVisible(False)
        self.right_panel = right_w

        top = QSplitter(Qt.Horizontal)
        top.addWidget(left_w)
        top.addWidget(right_w)
        top.setStretchFactor(0, 3)
        top.setStretchFactor(1, 1)

        buttons = QHBoxLayout()
        buttons.addWidget(self.btn_toggle_console)
        buttons.addStretch(1)
        buttons.addWidget(self.btn_apply)

        root = QVBoxLayout()
        root.addWidget(top)
        root.addLayout(buttons)
        root.addWidget(self.log)
        self.setLayout(root)

        self.loadFromJson()
        self.appendLog(self.tr("работает"))

    def pkgRoot(self):
        return os.path.abspath(os.path.join(os.path.dirname(os.path.abspath(__file__)), ".."))

    def jsonPath(self):
        return os.path.join(self.pkgRoot(), "res", "policies.json")

    def loadFromJson(self):
        self._items = []
        path = self.jsonPath()
        try:
            with open(path, "r", encoding="utf-8") as f:
                data = json.load(f)
            for item in data.get("policies", []):
                self._items.append(item)
        except Exception:
            self._items = []
        self.rebuildList()

    def rebuildList(self):
        self.list.clear()
        query = self.search.text().strip().lower()
        for item in self._items:
            title = item.get("title", "")
            if query and query not in title.lower():
                continue
            w = QListWidgetItem(title)
            w.setData(Qt.UserRole, item.get("id"))
            w.setFlags(w.flags() | Qt.ItemIsUserCheckable)
            w.setCheckState(Qt.Unchecked)
            self.list.addItem(w)
        if self.list.count() > 0:
            self.list.setCurrentRow(0)

    def filterList(self, _):
        self.rebuildList()

    def getItem(self, pid):
        for item in self._items:
            if item.get("id") == pid:
                return item
        return None

    def onItemClicked(self, it):
        pid = it.data(Qt.UserRole)
        self._current_id = pid
        data = self.getItem(pid)
        if not data:
            return
        self.info_title.setText(data.get("title", ""))
        self.info_text.setPlainText(data.get("description", ""))
        if not self.right_panel.isVisible():
            self.right_panel.setVisible(True)

    def appendLog(self, text):
        self.log.append(text)

    def selectedIds(self):
        ids = []
        for i in range(self.list.count()):
            it = self.list.item(i)
            if it.checkState() == Qt.Checked:
                ids.append(it.data(Qt.UserRole))
        return ids

    def toggleConsole(self):
        vis = self.log.isVisible()
        self.log.setVisible(not vis)
        if self.log.isVisible():
            self.btn_toggle_console.setText(self.tr("Закрыть консоль"))
            self.appendLog(self.tr("отладка: консоль открыта"))
        else:
            self.btn_toggle_console.setText(self.tr("Открыть консоль"))


    def applySelected(self):
        ids = self.selectedIds()
        if not ids and self._current_id:
            ids = [self._current_id]
        if not ids:
            self.appendLog(self.tr("отладка: ничего не выбрано"))
            return
        started = False
        for pid in ids:
            item = self.getItem(pid)
            if not item:
                continue
            scope = item.get("scope", "system")
            need_root = scope == "system"
            for step in item.get("apply", []):
                if step.get("type") != "cmd":
                    continue
                args = step.get("run", [])
                if not args:
                    continue
                if need_root:
                    QProcess.startDetached("pkexec", args)
                else:
                    program = args[0]
                    arguments = args[1:] if len(args) > 1 else []
                    QProcess.startDetached(program, arguments)
                self.appendLog(" ".join(args))
                started = True
        if started:
            self.appendLog(self.tr("применение начато"))
        else:
            self.appendLog(self.tr("отладка: нет действий"))

class PluginPolicies(plugins.Base):
    def __init__(self, plist: QStandardItemModel = None, pane: QStackedWidget = None):
        super().__init__("policies", 80, plist, pane)
        if self.plist != None and self.pane != None:
            self.node = QStandardItem(self.tr("Политики"))
            self.node.setData(self.name)
            self.plist.appendRow([self.node])
            self.pane.addWidget(QWidget())

    def _do_start(self, idx: int):
        main_window = self.pane.window()
        main_widget = PoliciesWindow(main_window)
        self.pane.insertWidget(idx, main_widget)
