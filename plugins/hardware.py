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
    """Hardware pane"""
    hardware_pane = None
    hardware_info = None

    def __init__(self):
        pass

    def start(self, plist, pane):
        # Add to main plugin listqqй
        node = QStandardItem("Hardware")
        plist.appendRow([node])
        # TODO: connect item selection to appropriate pane activation
        
        self.hardware_info = QTextBrowser()
        # Show output in monospace font
        self.hardware_info.setCurrentFont(QFont("monospace", 9))
        index = pane.addWidget(self.hardware_info)
        pane.setCurrentIndex(index)
        
        # Read info from inxi -F
        result = subprocess.check_output("inxi -F", shell=True, text=True)
        self.hardware_info.setText(result)
        
