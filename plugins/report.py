#!/usr/bin/python3

import plugins
from PyQt6.QtWidgets import QWidget, QVBoxLayout, QPushButton, QStackedWidget, QFileDialog, QMessageBox
from PyQt6.QtGui import QStandardItem, QStandardItemModel
from PyQt6.QtCore import QLocale

import json
import os


class ReportWidget(QWidget):
    def __init__(self, main_window = None):
        super().__init__()
        self.main_window = main_window

        layout = QVBoxLayout()

        self.report_btn = QPushButton(self.tr("Create report"))
        self.report_btn.clicked.connect(self.createReport)
        layout.addWidget(self.report_btn)

        layout.addStretch()
        self.setLayout(layout)

    def createReport(self):
        path, _ = QFileDialog.getSaveFileName(
            self,
            self.tr("Save report"),
            "altcenter-report.json",
            "JSON (*.json)"
        )

        if not path:
            return

        if not path.lower().endswith(".json"):
            path += ".json"

        try:
            report = {
                "policies": self.getPoliciesReport(),
                "journald": self.getPluginReport("journals_settings"),
                "auditd": self.getPluginReport("auditd_settings"),
                "fstec": self.getFstecReport(),
            }
        except Exception as e:
            QMessageBox.warning(self, self.tr("Report"), str(e))
            return

        try:
            with open(path, "w", encoding="utf-8") as f:
                json.dump(report, f, ensure_ascii=False, indent=4)
        except Exception as e:
            QMessageBox.warning(self, self.tr("Report"), str(e))
            return

        QMessageBox.information(self, self.tr("Report"), self.tr("Report saved"))

    def getPluginReport(self, plugin_name):
        for i, plugin in enumerate(self.main_window._plugs):
            if plugin.name != plugin_name:
                continue

            if plugin.started == False:
                try:
                    self.main_window.stack.removeWidget(
                        self.main_window.stack.widget(i)
                    )
                except:
                    pass

                plugin.run(i)

            widget = self.main_window.stack.widget(i)

            if hasattr(widget, "getReportData"):
                return widget.getReportData()

            return {}

        return {}

    def getPoliciesReport(self):
        for i, plugin in enumerate(self.main_window._plugs):
            if plugin.name != "policies":
                continue

            if plugin.started == False:
                try:
                    self.main_window.stack.removeWidget(
                        self.main_window.stack.widget(i)
                    )
                except:
                    pass

                plugin.run(i)

            widget = self.main_window.stack.widget(i)

            if hasattr(widget, "getReportData"):
                return widget.getReportData()

        return []

    def getFstecReport(self):
        fstec_report = {
            "boot": [],
            "sysctl": [],
            "kernel": [],
        }

        try:
            with open("/tmp/altcenter_fstec_check.json", "r", encoding="utf-8", errors="replace") as f:
                data = json.load(f)
        except:
            return fstec_report

        for group in ["boot", "sysctl", "kernel"]:
            for row in data.get(group, []):
                if not isinstance(row, (list, tuple)):
                    continue

                values = []

                for i in range(5):
                    value = row[i] if len(row) > i else ""
                    values.append("" if value is None else str(value))

                fstec_report[group].append({
                    "option": values[0],
                    "current_value": values[1],
                    "recommended_value": values[2],
                    "check_result": values[3],
                    "alternative": values[4]
                })

        return fstec_report


class PluginReport(plugins.Base):
    requires_admin = True

    def __init__(self, plist: QStandardItemModel=None, pane: QStackedWidget = None):
        super().__init__("report", 140, plist, pane)

        if self.plist != None and self.pane != None:
            self.node = QStandardItem(self.tr("Report"))
            self.node.setData(self.name)
            self.plist.appendRow([self.node])
            self.pane.addWidget(QWidget())

    def _do_start(self, idx: int):
        main_window = self.pane.window()
        main_widget = ReportWidget(main_window)
        self.pane.insertWidget(idx, main_widget)