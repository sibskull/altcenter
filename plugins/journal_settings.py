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

        self.proc = None
        self.proc_vacuum = None
        self.proc_retention = None

        self.usage_value = None
        self.vacuum_value = None
        self.btn_vacuum = None
        self.lbl_vacuum_status = None

        self.retention_value = None
        self.retention_unit = None
        self.btn_retention = None
        self.lbl_retention_status = None

        self.systemmaxuse_value = None
        self.btn_systemmaxuse = None
        self.lbl_systemmaxuse_status = None

        self.proc_systemmaxuse = None

        self.initUI()
        self.loadUsage()

    def initUI(self):
        layout = QVBoxLayout()
        layout.setContentsMargins(10, 10, 10, 10)

        top = QHBoxLayout()

        top.addWidget(QLabel(self.tr("Current log usage:")))

        self.usage_value = QLineEdit()
        self.usage_value.setReadOnly(True)
        self.usage_value.setText("")
        top.addWidget(self.usage_value, 1)

        top.addStretch(1)
        layout.addLayout(top)

        vacuum = QHBoxLayout()

        vacuum.addWidget(QLabel(self.tr("Vacuum to size (MB):")))

        self.vacuum_value = QLineEdit()
        self.vacuum_value.setText("0")
        vacuum.addWidget(self.vacuum_value, 1)

        self.btn_vacuum = QPushButton(self.tr("Vacuum"))
        self.btn_vacuum.clicked.connect(self.on_vacuum_clicked)
        vacuum.addWidget(self.btn_vacuum)

        self.lbl_vacuum_status = QLabel("")
        self.lbl_vacuum_status.setTextInteractionFlags(Qt.TextSelectableByMouse)
        vacuum.addWidget(self.lbl_vacuum_status)

        vacuum.addStretch(1)
        layout.addLayout(vacuum)

        retention = QHBoxLayout()

        retention.addWidget(QLabel(self.tr("Retention time:")))

        self.retention_value = QLineEdit()
        self.retention_value.setText("")
        retention.addWidget(self.retention_value, 1)

        self.retention_unit = QComboBox()
        self.retention_unit.addItem(self.tr("Day"))
        self.retention_unit.addItem(self.tr("Week"))
        self.retention_unit.addItem(self.tr("Month"))
        retention.addWidget(self.retention_unit)

        self.btn_retention = QPushButton(self.tr("Apply"))
        self.btn_retention.clicked.connect(self.on_retention_clicked)
        retention.addWidget(self.btn_retention)

        self.lbl_retention_status = QLabel("")
        self.lbl_retention_status.setTextInteractionFlags(Qt.TextSelectableByMouse)
        retention.addWidget(self.lbl_retention_status)

        retention.addStretch(1)
        layout.addLayout(retention)

        systemmaxuse = QHBoxLayout()

        systemmaxuse.addWidget(QLabel(self.tr("SystemMaxUse (MB):")))

        self.systemmaxuse_value = QLineEdit()
        self.systemmaxuse_value.setText("")
        systemmaxuse.addWidget(self.systemmaxuse_value, 1)

        self.btn_systemmaxuse = QPushButton(self.tr("Apply"))
        self.btn_systemmaxuse.clicked.connect(self.on_systemmaxuse_clicked)
        systemmaxuse.addWidget(self.btn_systemmaxuse)

        self.lbl_systemmaxuse_status = QLabel("")
        self.lbl_systemmaxuse_status.setTextInteractionFlags(Qt.TextSelectableByMouse)
        systemmaxuse.addWidget(self.lbl_systemmaxuse_status)

        systemmaxuse.addStretch(1)
        layout.addLayout(systemmaxuse)

        layout.addStretch(1)
        self.setLayout(layout)

    def loadUsage(self):
        self.proc = QProcess(self)
        env = QProcessEnvironment.systemEnvironment()
        self.proc.setProcessEnvironment(env)
        self.proc.finished.connect(self.on_finished)
        self.proc.start("journalctl", ["--disk-usage"])

    def on_finished(self, exit_code, exit_status):
        out = self.proc.readAllStandardOutput().data().decode(errors="replace").strip()
        err = self.proc.readAllStandardError().data().decode(errors="replace").strip()

        if exit_code == 0 and out:
            size = out
            marker = "take up "
            i = out.find(marker)
            if i >= 0:
                j = out.find(" in", i + len(marker))
                if j > i:
                    size = out[i + len(marker):j].strip()
            self.usage_value.setText(size)
            return

        if err:
            self.usage_value.setText(err)
        else:
            self.usage_value.setText(self.tr("Failed to read log usage."))

    def on_vacuum_clicked(self):
        if self.proc_vacuum != None and self.proc_vacuum.state() != QProcess.NotRunning:
            return

        t = self.vacuum_value.text().strip()
        try:
            mb = int(t)
        except:
            self.lbl_vacuum_status.setText(self.tr("Enter a numeric value"))
            return

        if mb < 0:
            self.lbl_vacuum_status.setText(self.tr("Enter a numeric value"))
            return

        self.lbl_vacuum_status.setText("")
        self.btn_vacuum.setEnabled(False)

        self.proc_vacuum = QProcess(self)
        env = QProcessEnvironment.systemEnvironment()
        self.proc_vacuum.setProcessEnvironment(env)
        self.proc_vacuum.finished.connect(self.on_vacuum_finished)

        self.proc_vacuum.start("pkexec", ["journalctl", f"--vacuum-size={mb}M"])

    def on_vacuum_finished(self, exit_code, exit_status):
        err = self.proc_vacuum.readAllStandardError().data().decode(errors="replace").strip()

        self.btn_vacuum.setEnabled(True)

        if exit_code == 0:
            self.lbl_vacuum_status.setText(self.tr("Done"))
            self.loadUsage()
            return

        if err:
            self.lbl_vacuum_status.setText(err)
        else:
            self.lbl_vacuum_status.setText(self.tr("Failed"))

    def on_retention_clicked(self):
        if self.proc_retention != None and self.proc_retention.state() != QProcess.NotRunning:
            return

        t = self.retention_value.text().strip()
        try:
            n = int(t)
        except:
            self.lbl_retention_status.setText(self.tr("Enter a numeric value"))
            return

        if n < 0:
            self.lbl_retention_status.setText(self.tr("Enter a numeric value"))
            return

        unit = self.retention_unit.currentText()
        days = n

        if unit == self.tr("Week"):
            days = n * 7
        elif unit == self.tr("Month"):
            days = n * 30

        self.lbl_retention_status.setText("")
        self.btn_retention.setEnabled(False)

        self.proc_retention = QProcess(self)
        env = QProcessEnvironment.systemEnvironment()
        self.proc_retention.setProcessEnvironment(env)
        self.proc_retention.finished.connect(self.on_retention_finished)

        self.proc_retention.start("pkexec", ["journalctl", f"--vacuum-time={days}days"])

    def on_retention_finished(self, exit_code, exit_status):
        err = self.proc_retention.readAllStandardError().data().decode(errors="replace").strip()

        self.btn_retention.setEnabled(True)

        if exit_code == 0:
            self.lbl_retention_status.setText(self.tr("Done"))
            self.loadUsage()
            return

        if err:
            self.lbl_retention_status.setText(err)
        else:
            self.lbl_retention_status.setText(self.tr("Failed"))

    def on_systemmaxuse_clicked(self):
        if self.proc_systemmaxuse != None and self.proc_systemmaxuse.state() != QProcess.NotRunning:
            return

        t = self.systemmaxuse_value.text().strip()
        try:
            mb = int(t)
        except:
            self.lbl_systemmaxuse_status.setText(self.tr("Enter a numeric value"))
            return

        if mb < 0:
            self.lbl_systemmaxuse_status.setText(self.tr("Enter a numeric value"))
            return

        self.lbl_systemmaxuse_status.setText("")
        self.btn_systemmaxuse.setEnabled(False)

        self.proc_systemmaxuse = QProcess(self)
        env = QProcessEnvironment.systemEnvironment()
        self.proc_systemmaxuse.setProcessEnvironment(env)
        self.proc_systemmaxuse.finished.connect(self.on_systemmaxuse_finished)

        cmd = (
            "mkdir -p /etc/systemd/journald.conf.d && "
            f"printf '[Journal]\\nSystemMaxUse={mb}M\\n' > /etc/systemd/journald.conf.d/altcenter.conf && "
            "systemctl restart systemd-journald"
        )
        self.proc_systemmaxuse.start("pkexec", ["sh", "-c", cmd])

    def on_systemmaxuse_finished(self, exit_code, exit_status):
        err = self.proc_systemmaxuse.readAllStandardError().data().decode(errors="replace").strip()

        self.btn_systemmaxuse.setEnabled(True)

        if exit_code == 0:
            self.lbl_systemmaxuse_status.setText(self.tr("Done"))
            self.loadUsage()
            return

        if err:
            self.lbl_systemmaxuse_status.setText(err)
        else:
            self.lbl_systemmaxuse_status.setText(self.tr("Failed"))


class PluginJournals(plugins.Base):
    def __init__(self, plist: QStandardItemModel=None, pane: QStackedWidget = None):
        super().__init__("journals_settings", 110, plist, pane)

        if self.plist != None and self.pane != None:
            self.node = QStandardItem(self.tr("System logs settings"))
            self.node.setData(self.name)
            self.plist.appendRow([self.node])
            self.pane.addWidget(QWidget())

    def _do_start(self, idx: int):
        main_window = self.pane.window()
        main_widget = JournalsWidget(main_window)
        self.pane.insertWidget(idx, main_widget)
