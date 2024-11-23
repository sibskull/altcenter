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
from PyQt5.QtWidgets import QWidget, QTextBrowser, QDialog, QLabel, QFrame, QSizePolicy
from PyQt5.QtGui import QStandardItem, QFont
from PyQt5.uic import loadUi
from PyQt5.QtCore import QT_VERSION_STR
from PyQt5.QtCore import Qt
from PyQt5.QtCore import QTranslator, QLocale, QCoreApplication

import locale
import os, re, subprocess


class HardwareWidget(QDialog):

    def __init__(self):
        super(HardwareWidget,self).__init__()

        current_file = os.path.abspath(__file__)
        current_dir = os.path.dirname(current_file)
        parent_dir_of_module_dir = os.path.dirname(current_dir)
        loadUi(os.path.join(parent_dir_of_module_dir, 'ui_hardware.ui'), self)


def parse_os_release() -> dict:
    os_info = {}
    with open('/etc/os-release', 'r') as f:
        for line in f:
            line = line.strip()
            if not line or line.startswith('#'):
                continue

            key, value = line.split('=', 1)

            value = value.strip('"')

            os_info[key] = value

    return os_info


def get_display_server() -> str:
    session_type = os.getenv('XDG_SESSION_TYPE')
    if session_type:
        return session_type
    else:
        return "Not detected"


def get_cpu_info_from_proc():
    with open("/proc/cpuinfo", "r") as f:
        cpu_info = f.read()

    cpu_name = None
    for line in cpu_info.splitlines():
        if line.startswith("model name"):
            cpu_name = line.split(":")[1].strip()
            break

    num_cores = cpu_info.count("processor")

    return cpu_name, num_cores


def get_memory_info_from_free():
    try:
        result = subprocess.run(['free', '-b'], capture_output=True, text=True)
        memory_info = result.stdout

        lines = memory_info.splitlines()
        total_memory = int(lines[1].split()[1])
        used_memory = int(lines[1].split()[2])
        free_memory = int(lines[1].split()[3])

        return total_memory, used_memory, free_memory
    except FileNotFoundError:
        return "free command not found", None, None


def get_video_info_from_inxi():
    try:
        result = subprocess.run(['inxi', '-G', '-c'], capture_output=True, text=True)
        output = result.stdout
#         output = """Graphics:
#   Device-1: Intel CometLake-H GT2 [UHD Graphics] driver: i915 v: kernel
#   Device-2: NVIDIA TU116M [GeForce GTX 1660 Ti Mobile] driver: nouveau
#     v: kernel
#   Device-3: Chicony HP Wide Vision HD Camera driver: uvcvideo type: USB
#   Display: x11 server: X.Org v: 1.21.1.14 driver: X:
#     loaded: modesetting,nouveau unloaded: fbdev,vesa dri: iris,nouveau gpu: i915
#     resolution: 1920x1080~60Hz
#   API: EGL v: 1.5 drivers: iris,nouveau,swrast
#     platforms: gbm,x11,surfaceless,device
#   API: OpenGL v: 4.6 compat-v: 4.3 vendor: intel mesa v: 24.2.6
#     renderer: Mesa Intel UHD Graphics (CML GT2)
# """
        gpu_info = re.findall(r'Device-\d+:\s*(.*?)\s*driver:\s*(\S+)\s*v:\s*(\S+)', output)
        # for device in gpu_info:
        #     device_name, driver, version = device
        #     print(f"Устройство: {device_name}\nДрайвер: {driver}\nВерсия: {version}\n")

        return gpu_info
    except FileNotFoundError:
        return "inxi command not found", None, None


class PluginHardware(plugins.Base):
    """Hardware pane"""
    # hardware_pane = None
    hardware_info = None

    def __init__(self):
        super().__init__()
        pass

    def HLine(self):
        hLine = QFrame()
        hLine.setFrameShape(QFrame.Shape.HLine)
        hLine.setFrameShadow(QFrame.Shadow.Sunken)
        return hLine

    def start(self, plist, pane):
        # Add to main plugin list
        node = QStandardItem(self.tr("Hardware"))
        plist.appendRow([node])
        # TODO: connect item selection to appropriate pane activation

        # self.hardware_info = QTextBrowser()
        # # Show output in monospace font
        # self.hardware_info.setCurrentFont(QFont("monospace", 9))
        # index = pane.addWidget(self.hardware_info)
        # # pane.setCurrentIndex(index)

        # # Read info from inxi -F
        # result = subprocess.check_output("inxi -F", shell=True, text=True)
        # self.hardware_info.setText(result)

        os_info = parse_os_release()
        # for key, value in os_info.items():
        #     print(f"{key}: {value}")

        hw = HardwareWidget()

        fontTitle = hw.font()
        fontTitle.setPointSize(fontTitle.pointSize() + 2)

        hw.lblAltValue.setText("{} {} {}".format(os_info["PRETTY_NAME"], os_info["NAME"], os_info["VERSION"]))
        # print("{} {} {}".format(os_info["PRETTY_NAME"], os_info["NAME"], os_info["VERSION"]))


        # Software section
        #
        titleSection = QLabel(self.tr("Software"))
        titleSection.setFont(fontTitle)
        titleSection.setAlignment(Qt.AlignmentFlag.AlignCenter)
        hw.formLayout.addRow(titleSection)
        hw.formLayout.addRow(self.HLine())

        hw.formLayout.addRow(self.tr("Qt version:"), QLabel(QT_VERSION_STR))

        uname = os.uname()
        hw.formLayout.addRow(self.tr("Kernel:"), QLabel(uname.release))

        hw.formLayout.addRow(self.tr("Display server:"), QLabel(get_display_server()))


        # Hardware section
        #
        titleSection = QLabel(self.tr("Hardware"))
        titleSection.setFont(fontTitle)
        titleSection.setAlignment(Qt.AlignmentFlag.AlignCenter)
        hw.formLayout.addRow(titleSection)
        hw.formLayout.addRow(self.HLine())

        cpu_name, num_cores = get_cpu_info_from_proc()
        hw.formLayout.addRow(self.tr("Processor:"), QLabel("{} x {}".format(num_cores, cpu_name)))

        total_memory, used_memory, free_memory = get_memory_info_from_free()
        hw.formLayout.addRow(self.tr("Memory (used/total):"),
                             QLabel(f"{used_memory / (1024 ** 3):.2f} {self.tr("GB")}  /  {total_memory / (1024 ** 3):.2f} GB"))

        gpu_info = get_video_info_from_inxi()
        i = 0
        for device in gpu_info:
            i += 1
            s = self.tr("Graphics")
            if len(gpu_info) > 1:
                s = f"{s}-{i}"
            gr = QLabel(s)
            gr.setAlignment(Qt.AlignmentFlag.AlignCenter)
            hw.formLayout.addRow(gr, QLabel())

            device_name, driver, version = device
            # print(f"Устройство: {device_name}\nДрайвер: {driver}\nВерсия: {version}\n")
            lblHwGpuDevice = QLabel(device_name)
            hw.formLayout.addRow(self.tr("Device:"), lblHwGpuDevice)
            lblHwGpuDriver = QLabel(driver)
            hw.formLayout.addRow(self.tr("Driver:"), lblHwGpuDriver)
            lblHwGpuDriverVersion = QLabel(version)
            # lblHwGpuDriverVersion.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)
            hw.formLayout.addRow(self.tr("Version:"), lblHwGpuDriverVersion)

        pane.addWidget(hw)
