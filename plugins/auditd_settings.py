#!/usr/bin/python3

import plugins
import os
import json
from PyQt5.QtWidgets import QWidget, QVBoxLayout, QHBoxLayout, QStackedWidget, QListWidget, QListWidgetItem, QTextEdit, QSplitter, QLabel, QPushButton, QLineEdit, QComboBox
from PyQt5.QtGui import QStandardItem, QStandardItemModel, QFont
from PyQt5.QtCore import Qt, QProcess, QProcessEnvironment, QLocale

class JournalsWidget(QWidget):
    def __init__(self, main_window = None):
        super().__init__()
        self.main_window = main_window

        self.max_log_file_value = None
        self.num_logs_value = None
        self.space_left_value = None

        self.btn_apply = None
        self.lbl_status = None

        self.initUI()

    def initUI(self):
        layout = QVBoxLayout()
        layout.setContentsMargins(10, 10, 10, 10)

        max_log_file = QHBoxLayout()

        max_log_file.addWidget(QLabel(self.tr("Max log file size (MB):")))

        self.max_log_file_value = QLineEdit()
        self.max_log_file_value.setText("")
        max_log_file.addWidget(self.max_log_file_value, 1)

        max_log_file.addStretch(1)
        layout.addLayout(max_log_file)

        num_logs = QHBoxLayout()

        num_logs.addWidget(QLabel(self.tr("Max log files count:")))

        self.num_logs_value = QLineEdit()
        self.num_logs_value.setText("")
        num_logs.addWidget(self.num_logs_value, 1)

        num_logs.addStretch(1)
        layout.addLayout(num_logs)

        space_left = QHBoxLayout()

        space_left.addWidget(QLabel(self.tr("Minimum free space (MB):")))

        self.space_left_value = QLineEdit()
        self.space_left_value.setText("")
        space_left.addWidget(self.space_left_value, 1)

        space_left.addStretch(1)
        layout.addLayout(space_left)

        apply_layout = QHBoxLayout()

        self.btn_apply = QPushButton(self.tr("Apply"))
        self.btn_apply.clicked.connect(self.on_apply_clicked)
        apply_layout.addWidget(self.btn_apply)

        self.lbl_status = QLabel("")
        self.lbl_status.setTextInteractionFlags(Qt.TextSelectableByMouse)
        apply_layout.addWidget(self.lbl_status)

        apply_layout.addStretch(1)
        layout.addLayout(apply_layout)

        layout.addStretch(1)
        self.setLayout(layout)

    def on_apply_clicked(self):
        t = self.max_log_file_value.text().strip()
        try:
            max_log_file = int(t)
        except:
            self.lbl_status.setText(self.tr("Enter a numeric value"))
            return

        if max_log_file < 0:
            self.lbl_status.setText(self.tr("Enter a numeric value"))
            return

        t = self.num_logs_value.text().strip()
        try:
            num_logs = int(t)
        except:
            self.lbl_status.setText(self.tr("Enter a numeric value"))
            return

        if num_logs < 0:
            self.lbl_status.setText(self.tr("Enter a numeric value"))
            return

        t = self.space_left_value.text().strip()
        try:
            space_left = int(t)
        except:
            self.lbl_status.setText(self.tr("Enter a numeric value"))
            return

        if space_left < 0:
            self.lbl_status.setText(self.tr("Enter a numeric value"))
            return

        self.lbl_status.setText(self.tr("test"))


class PluginJournals(plugins.Base):
    requires_admin = True
    def __init__(self, plist: QStandardItemModel=None, pane: QStackedWidget = None):
        super().__init__("auditd_settings", 120, plist, pane)

        if self.plist != None and self.pane != None:
            self.node = QStandardItem(self.tr("Auditd logs settings"))
            self.node.setData(self.name)
            self.plist.appendRow([self.node])
            self.pane.addWidget(QWidget())

    def _do_start(self, idx: int):
        main_window = self.pane.window()
        main_widget = JournalsWidget(main_window)
        self.pane.insertWidget(idx, main_widget)