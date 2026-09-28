from PyQt6.QtWidgets import QWidget, QVBoxLayout, QHBoxLayout, QStackedWidget, QListWidget, QListWidgetItem, QTextEdit, QSplitter, QLabel, QPushButton, QLineEdit, QComboBox, QToolButton, QCheckBox, QFileDialog
from PyQt6.QtGui import QStandardItem, QStandardItemModel, QFont, QTextCursor, QTextCharFormat, QColor, QPalette
from PyQt6.QtCore import Qt, QProcess, QProcessEnvironment, QLocale, QPoint

import plugins

class SSHSettingsWidget(QWidget):
    def __init__(self, main_window=None):
        super().__init__(main_window)

        self.main_window = main_window
        pass


class PluginSSHSettings(plugins.Base):
    def __init__(self, plist: QStandardItemModel=None, pane: QStackedWidget = None):
        super().__init__("ssh_settings", 150, plist, pane)

        if self.plist != None and self.pane != None:
            self.node = QStandardItem(self.tr("SSH settings"))
            self.node.setData(self.name)
            self.add_to_menu(self.node)
            self.pane.addWidget(QWidget())

    def _do_start(self, idx: int):
        main_window = self.pane.window()
        main_widget = SSHSettingsWidget(main_window)
        self.pane.insertWidget(idx, main_widget)