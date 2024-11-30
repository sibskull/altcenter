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

from PyQt5.QtWidgets import QApplication, QWidget, QFrame, QLabel
from PyQt5.QtCore import QTranslator, Qt, QT_VERSION_STR
# from PyQt5 import uic
from PyQt5.QtGui import QStandardItemModel, QStandardItem

import os
import sys
import locale

from ui_mainwindow import Ui_MainWindow
from plugins import Base
import my_utils

data_dir = "/usr/share/altcenter"
data_dir = "."
plugin_path = os.path.join(data_dir, "plugins")

class MainWindow(QWidget, Ui_MainWindow):
    """Main window"""
    def __init__(self):
        #super(MainWindow, self).__init__() # Call the inherited classes __init__ method
        super().__init__()
        self.setupUi(self)

        # Load UI from file
        # uic.loadUi("ui_mainwindow.ui", self) # Load the .ui file

        self.splitter.setStretchFactor(0,0)
        self.splitter.setStretchFactor(1,1)

        self.about()


    def onSelectionChange(self, index):
        """Slot for change selection"""
        self.stack.setCurrentIndex(index.row())


    def HLine(self):
        hLine = QFrame()
        hLine.setFrameShape(QFrame.Shape.HLine)
        hLine.setFrameShadow(QFrame.Shadow.Sunken)
        return hLine


    def about(self):
        # Chdir to data_dir
        os.chdir(data_dir)


        # Set module list model
        self.list_module = QStandardItemModel()
        self.moduleList.setModel(self.list_module)
        self.moduleList.selectionModel().currentChanged.connect(self.onSelectionChange)

        node = QStandardItem(self.tr("About system"))
        self.list_module.appendRow([node])

        fontTitle = self.font()
        fontTitle.setPointSize(fontTitle.pointSize() + 2)

        os_info = my_utils.parse_os_release()

        self.lblAltValue.setText("{} {} {}".format(os_info["PRETTY_NAME"], os_info["NAME"], os_info["VERSION"]))

        # Software section
        #
        # titleSection = QLabel(self.tr("Software"))
        # titleSection.setFont(fontTitle)
        # titleSection.setAlignment(Qt.AlignmentFlag.AlignCenter)
        # titleSection.setStyleSheet("QLabel {padding: 15px 0px 0px 0px;}")
        # self.formLayout.addRow(titleSection)
        # self.formLayout.addRow(self.HLine())

        # self.formLayout.addRow(self.tr("Qt version:"), QLabel(QT_VERSION_STR))

        uname = os.uname()
        self.formLayout.addRow(self.tr("Kernel:"), QLabel(uname.release))

        self.formLayout.addRow(self.tr("Display server:"), QLabel(my_utils.get_display_server()))

        # Hardware section
        #
        # titleSection = QLabel(self.tr("Hardware"))
        # titleSection.setFont(fontTitle)
        # titleSection.setAlignment(Qt.AlignmentFlag.AlignCenter)
        # titleSection.setStyleSheet("QLabel {padding: 15px 0px 0px 0px;}")
        # self.formLayout.addRow(titleSection)
        # self.formLayout.addRow(self.HLine())

        # cpu_name, num_cores = my_utils.get_cpu_info_from_proc()
        # self.formLayout.addRow(self.tr("Processor:"), QLabel("{} x {}".format(num_cores, cpu_name)))

        total_memory, used_memory, free_memory = my_utils.get_memory_info_from_free()
        gb = self.tr("GB")
        self.formLayout.addRow(self.tr("Memory (used/total):"),
                                QLabel(f"{used_memory / (1024 ** 3):.2f} {gb}  /  {total_memory / (1024 ** 3):.2f} {gb}"))

        # gpu_info = my_utils.get_video_info_from_inxi()
        # i = 0
        # for device in gpu_info:
        #     i += 1
        #     s = self.tr("Graphics")
        #     if len(gpu_info) > 1:
        #         s = f"{s}-{i}"
        #     gr = QLabel(s)
        #     gr.setAlignment(Qt.AlignmentFlag.AlignCenter)
        #     self.formLayout.addRow(gr, QLabel())

        #     device_name, driver, version = device
        #     # print(f"Устройство: {device_name}\nДрайвер: {driver}\nВерсия: {version}\n")
        #     lblHwGpuDevice = QLabel(device_name)
        #     self.formLayout.addRow(self.tr("Device:"), lblHwGpuDevice)
        #     lblHwGpuDriver = QLabel(driver)
        #     self.formLayout.addRow(self.tr("Driver:"), lblHwGpuDriver)
        #     lblHwGpuDriverVersion = QLabel(version)
        #     # lblHwGpuDriverVersion.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)
        #     self.formLayout.addRow(self.tr("Version:"), lblHwGpuDriverVersion)


# Run application
app = QApplication(sys.argv) # Create an instance of QtWidgets.QApplication


# Load current locale translation
current_file = os.path.abspath(__file__)
current_dir = os.path.dirname(current_file)

translator = QTranslator(app)
tr_file = os.path.join(current_dir, "altcenter_" + locale.getlocale()[0].split( '_' )[0])
# print( "Load translation from %s.qm" % ( tr_file ) )
if translator.load( tr_file ):
    app.installTranslator(translator)


# Initialize UI
window = MainWindow() # Create an instance of our class

# Load plugins
for p in Base.plugins:
    inst = p()
    inst.start(window.list_module, window.stack)


window.splitter.setStretchFactor(0,0)
window.splitter.setStretchFactor(1,1)

# Show window
window.show()

# Start the application
sys.exit(app.exec_())
