import plugins
from PyQt5.QtGui import QStandardItem


class PluginDocumentation(plugins.Base):
    def __init__(self):
        super().__init__("Components", 80)
        self.node = None

    def start(self, plist, pane):
        self.node = QStandardItem(self.tr("Components"))
        self.node.setData(self.getName())
        plist.appendRow([self.node])
