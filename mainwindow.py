# Application for configure and maintain ALT operating system
# (c) 2024-2025 Andrey Cherepanov <cas@altlinux.org>
# (c) 2024-2025 Sergey Shevchenko <Sergey.Shevchenko04@gmail.com>

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

from PyQt5.QtWidgets import QApplication, QWidget, QMessageBox
from PyQt5.QtCore import QTranslator, QSettings, QObject, QEvent, Qt
from PyQt5.QtCore import QCommandLineParser, QCommandLineOption
from PyQt5.QtWebEngineWidgets import QWebEngineView
from PyQt5.QtCore import QLibraryInfo, QLocale
# from PyQt5 import uic
from PyQt5.QtGui import QStandardItemModel, QIcon

import os
import sys
import locale
import pathlib

from ui_mainwindow import Ui_MainWindow
from plugins import Base

current_dir = os.path.dirname(os.path.abspath(__file__))
plugin_path = os.path.join(current_dir, "plugins")

if os.environ.get("XDG_SESSION_TYPE") == "wayland":
    os.environ["QT_QPA_PLATFORM"] = "xcb"


class QtContextMenuRuFilter(QObject):

    def __init__(self, parent=None):
        super().__init__(parent)
        self._patched_web = set()
        self._map = {
            'Undo': 'Отменить',
            'Redo': 'Повторить',
            'Cut': 'Вырезать',
            'Copy': 'Копировать',
            'Paste': 'Вставить',
            'Delete': 'Удалить',
            'Clear': 'Очистить',
            'Select All': 'Выделить всё',
            'Paste and Match Style': 'Вставить без форматирования',

            'Back': 'Назад',
            'Forward': 'Вперёд',
            'Reload': 'Обновить',
            'Save page': 'Сохранить страницу',
            'View page source': 'Просмотреть исходный код страницы',
            'Copy Link Location': 'Копировать адрес ссылки'
        }

    def eventFilter(self, obj, event):
        t = event.type()

        if QLocale.system().language() != QLocale.Russian:
            return False

        if t == QEvent.ChildAdded:
            if hasattr(event, 'child'):
                ch = event.child()
                if isinstance(ch, QWebEngineView):
                    self._patch_webengine(ch)
            return False

        if t == QEvent.Show:
            if isinstance(obj, QWebEngineView):
                self._patch_webengine(obj)
            return False

        if t != QEvent.ContextMenu:
            return False

        if isinstance(obj, QWebEngineView):
            return False

        w = obj
        for _ in range(12):
            if w is None:
                break
            if hasattr(w, 'contextMenuPolicy') and w.contextMenuPolicy() != Qt.DefaultContextMenu:
                return False
            if hasattr(w, 'createStandardContextMenu'):
                try:
                    menu = w.createStandardContextMenu()
                except Exception:
                    return False
                if menu is None:
                    return False
                self._translate_menu(menu)
                menu.exec_(event.globalPos())
                menu.deleteLater()
                return True
            w = w.parent()

        return False

    def _patch_webengine(self, view):
        vid = int(view.winId()) if hasattr(view, 'winId') else id(view)
        if vid in self._patched_web:
            return
        self._patched_web.add(vid)
        view.setContextMenuPolicy(Qt.CustomContextMenu)
        view.customContextMenuRequested.connect(self._on_web_context_menu)

    def _on_web_context_menu(self, pos):
        view = self.sender()
        if view is None:
            return
        try:
            page = view.page()
        except Exception:
            page = None
        if page is None:
            return
        try:
            menu = page.createStandardContextMenu()
        except Exception:
            return
        if menu is None:
            return
        self._translate_menu(menu)
        menu.exec_(view.mapToGlobal(pos))
        menu.deleteLater()

    def _translate_menu(self, menu):
        for act in menu.actions():
            sub = act.menu()
            if sub is not None:
                self._translate_menu(sub)
                continue

            txt = act.text()
            if not txt:
                continue

            clean = txt.replace('&', '')
            left = clean.split('\t', 1)[0]

            suffix = ''
            if left.endswith('...'):
                suffix = '...'
                left = left[:-3]
            elif left.endswith('…'):
                suffix = '…'
                left = left[:-1]

            ru = self._map.get(left)
            if not ru:
                continue

            if '\t' in txt:
                act.setText(ru + suffix + '\t' + txt.split('\t', 1)[1])
            else:
                act.setText(ru + suffix)


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

        self.block_close = False

    def onSelectionChange(self, index):
        """Slot for change selection"""
        idx = index.row()
        plugin = plugs[idx]
        if plugin.started == False:
            self.stack.removeWidget(self.stack.widget(idx))
            plugin.run(idx)

        self.stack.setCurrentIndex(idx)

    def onSessionStartChange(self, state):
        """Slot to change autostart checkbox change"""
        self.settings.setValue('Settings/runOnSessionStart', (state == 2))
        self.settings.sync()

    def closeEvent(self, event):
        if self.block_close:
            QMessageBox.warning(self, "Операция выполняется", "Нельзя закрыть окно во время установки или обновления.")
            event.ignore()
        else:
            event.accept()

# Run application
app = QApplication(sys.argv) # Create an instance of QtWidgets.QApplication
app.setApplicationName(APPLICATION_NAME)
app.setApplicationVersion(APPLICATION_VERSION)
app.setDesktopFileName("altcenter")

# Load settings
current_config = os.path.join(pathlib.Path.home(), ".config", "altcenter.ini")
settings = QSettings(current_config, QSettings.IniFormat)

# Translation context menu
_qt_translators = []

qt_domains = ("qtbase", "qtwebengine")
system_locale = QLocale.system()
translations_dir = QLibraryInfo.location(QLibraryInfo.TranslationsPath)

for dom in qt_domains:
    tr = QTranslator()
    if tr.load(system_locale, dom, "_", translations_dir):
        app.installTranslator(tr)
        _qt_translators.append(tr)

if system_locale.language() == QLocale.Russian:
    app._qt_menu_filter = QtContextMenuRuFilter(app)
    app.installEventFilter(app._qt_menu_filter)

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
at_startup = QCommandLineOption('at-startup', app.translate('app', "Run at session startup"))
list_modules = QCommandLineOption(['m', 'modules'], app.translate('app', "List available modules and exit"))
parser.addOption(at_startup)
parser.addOption(list_modules)

# Process the actual command line arguments given by the user
parser.process(app)

# Additional arguments (like module_name)
#print(parser.positionalArguments())
if len(parser.positionalArguments()) > 0:
    module_name = parser.positionalArguments()[0]
else:
    module_name = 'about'  # First module name

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
        print(inst.name)

    sys.exit(0)


# Load plugins
k = 0
selected_index = 0

plugs = []

for p in Base.plugins:
    inst = p(window.list_module_model, window.stack)
    # inst.start(window.list_module_model, window.stack)
    plugs.append(inst)
    # Select item by its name
    if inst.name == module_name:
        selected_index = k
    k = k + 1

index = window.list_module_model.index(selected_index, 0)
window.moduleList.setCurrentIndex(index)


window.splitter.setStretchFactor(0,0)
window.splitter.setStretchFactor(1,1)

# Reset logo by absolute path
window.altLogo.setPixmap(QIcon.fromTheme("basealt").pixmap(64))

# Show window
window.show()

# Start the application
sys.exit(app.exec_())
