#!/usr/bin/python3

# Application for configure and maintain ALT operating system
# (c) 2024 Andrey Cherepanov <cas@altlinux.org>

# This program is free software; you can redistribute it and/or modify it under
# the terms of the GNU General Public License as published by the Free Software
# Foundation; either version 3 of the License, or (at your option) any later
# version.

# This program is distributed in the hope that it will be useful, but WITHOUT
# ANY WARRANTY; without even the implied warranty of MERCHANTABILITY or FITNESS
# FOR A PARTICULAR PURPOSE. See the GNU General Public License for more
# details.

# You should have received a copy of the GNU General Public License along with
# this program; if not, write to the Free Software Foundation, Inc., 59 Temple
# Place - Suite 330, Boston, MA  02111-1307, USA.

import plugins
from PyQt5.QtWidgets import QWidget, QTextBrowser
from PyQt5.QtGui import QStandardItem, QFont
import subprocess

class PluginHardware(plugins.Base):
    # license_pane = None
    license_info = None
    index = 0

    def __init__(self):
        pass

    def start(self, plist, pane):
        # Licence
        node = QStandardItem("License")
        plist.appendRow([node])

        self.license_info = QTextBrowser()
        self.license_info.setCurrentFont(QFont("monospace", 9))
        self.index = pane.addWidget(self.license_info)
        pane.setCurrentIndex(self.index)
        licen = subprocess.check_output("cat /usr/share/alt-notes/license.ru.html", shell=True, text=True)
        self.license_info.setHtml(licen)
