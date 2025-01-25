# Application for configure and maintain ALT operating system
# (c) 2024-2025 Andrey Cherepanov <cas@altlinux.org>
# (c) 2024 Sergey Shevchenko <Sergey.Shevchenko04@gmail.com>

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

APPLICATION_NAME = 'altcenter'
APPLICATION_VERSION = '1.0'

from PyQt5.QtWidgets import QApplication, QWidget
from PyQt5.QtCore import QTranslator, QSettings
from PyQt5.QtCore import QCommandLineParser, QCommandLineOption
from PyQt5.QtCore import QItemSelectionModel
# from PyQt5 import uic
from PyQt5.QtGui import QStandardItemModel, QPixmap

import os
import sys
import locale
import pathlib

from ui_mainwindow import Ui_MainWindow
from plugins import Base

current_dir = os.path.dirname(os.path.abspath(__file__))
plugin_path = os.path.join(current_dir, "plugins")

module_name = "about" # First module name

class MainWindow(QWidget, Ui_MainWindow):
    """Main window"""
    settings = None

    def __init__(self):
        #super(MainWindow, self).__init__() # Call the inherited classes __init__ method
        super().__init__()
        self.setupUi(self)

        # Load UI from file
        # uic.loadUi("ui_mainwindow.ui", self) # Load the .ui file

        self.splitter.setStretchFactor(0,0)
        self.splitter.setStretchFactor(1,1)

    def onSelectionChange(self, index):
        """Slot for change selection"""
        self.stack.setCurrentIndex(index.row() + 1)

    def onSessionStartChange(self, state):
        """Slot to change autostart checkbox change"""
        self.settings.setValue('Settings/runOnSessionStart', (state == 2))
        self.settings.sync()

# Run application
app = QApplication(sys.argv) # Create an instance of QtWidgets.QApplication
app.setApplicationName(APPLICATION_NAME)
app.setApplicationVersion(APPLICATION_VERSION)
app.setDesktopFileName("altcenter")

# Load settings
current_config = os.path.join(pathlib.Path.home(), ".config", "altcenter.ini")
settings = QSettings(current_config, QSettings.IniFormat)

# Load current locale translation
translator = QTranslator(app)
tr_file = os.path.join(current_dir, "altcenter_" + locale.getlocale()[0].split( '_' )[0])
# print( "Load translation from %s.qm" % ( tr_file ) )
if translator.load( tr_file ):
    app.installTranslator(translator)

# Set command line argument parser
parser = QCommandLineParser()
parser.addHelpOption()
parser.addVersionOption()
at_startup = QCommandLineOption('at-startup', app.translate('app', 'Run at session startup'))
list_modules = QCommandLineOption('modules', app.translate('app', 'List available modules and exit'))
parser.addOption(at_startup)
parser.addOption(list_modules)

# Process the actual command line arguments given by the user
parser.process(app)

# Additional arguments (like module_name)
#print(parser.positionalArguments())
if len(parser.positionalArguments()) > 0:
    module_name = parser.positionalArguments()[0]

# Quit if "Do not run on next sesion start" is checked and application ran with --at-startup
value_runOnSessionStart = settings.value('Settings/runOnSessionStart', False, type=bool)
if parser.isSet(at_startup) and value_runOnSessionStart:
    sys.exit(0)

# Initialize UI
window = MainWindow() # Create an instance of our class

# Use settings file
window.settings = settings

# Set autostart checkbox state
window.runOnSessionStart.setChecked(value_runOnSessionStart)
window.runOnSessionStart.stateChanged.connect(window.onSessionStartChange)

# Set module list model
window.list_module_model = QStandardItemModel()
window.moduleList.setModel(window.list_module_model)
window.moduleList.selectionModel().currentChanged.connect(window.onSelectionChange)


# List available modules and exit
if parser.isSet(list_modules):
    for p in Base.plugins:
        inst = p()
        print(inst.getName())

    sys.exit(0)


# Load plugins
k = 0
for p in Base.plugins:
    inst = p()
    inst.start(window.list_module_model, window.stack)
    # Select item by its name
    if inst.getName() == module_name:
        ix = window.list_module_model.index(k, 0)
        sm = window.moduleList.selectionModel()
        # TODO: set focus to selected item and show appropriate stack pane
        #sm.select(ix, QItemSelectionModel.ClearAndSelect)
        #window.stack.setCurrentIndex(k+1)
    k = k+1


window.splitter.setStretchFactor(0,0)
window.splitter.setStretchFactor(1,1)

# Reset logo by absolute path
window.altLogo.setPixmap(QPixmap(os.path.join(current_dir, "basealt.png")))

# Show window
window.show()

# Start the application
sys.exit(app.exec_())
