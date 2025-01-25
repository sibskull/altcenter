#!/usr/bin/python3

import plugins
from PyQt5.QtWidgets import (QWidget, QVBoxLayout, QGroupBox,
                            QGridLayout, QScrollArea, QTextBrowser)
from PyQt5.QtGui import QStandardItem, QFont
from PyQt5.QtCore import QObject
import subprocess

class GetSystemInfo(QObject):
    def __init__(self):
        super().__init__()

    def get_system_info(self) -> str:

        # Получаем информацию о системе через inxi -F
        try:
            system_info = subprocess.check_output(
                "inxi -F -c -y -1",
                shell=True,
                text=True
            )
            # Очищаем от специальных символов
            # system_info = re.sub(r'', '', system_info)
            # system_info = re.sub(r'12', '', system_info)

            # Расширенный список терминов для разделителей
            separators = [
                'System:',
                'Machine:',
                'Battery:',
                'CPU:',
                'Graphics:',
                'Audio:',
                'Network:',
                'Bluetooth:',
                'Drives:',
                'Partition:',
                'Swap:',
                'Sensors:',
                'Info:',
            ]

            info = system_info.split('\n')

            # Добавляем белую разделительную линию
            for separator in separators:
                sep_len = len(separator)
                for key, value in enumerate(info):
                    # print(key, "    ", value)
                    if value[0:sep_len] == separator:
                        s = '<hr style="border: 1px solid #000000; margin: 10px 0;">' + separator
                        info.insert(key, s)
                        # print(value)
                        info[key+1] = ' ' * sep_len + value[sep_len:]
                        # print(info[key])
                        break


            # Словари переводов для разных языков
            translations = {
                # Special terms
                'System Temperatures:': self.tr('<b>System Temperatures:</b>'),
                'Fan Speeds (rpm):': self.tr('<b>Fan Speeds (rpm):</b>'),
                'N/A': self.tr('N/A'),

                # Headers with HTML formatting
                'System:': self.tr('<b>System:</b>'),
                'Kernel:': self.tr('<b>Kernel:</b>'),
                'Desktop:': self.tr('<b>Desktop:</b>'),
                'CPU:': self.tr('<b>CPU:</b>'),
                'GPU:': self.tr('<b>GPU:</b>'),
                'Memory:': self.tr('<b>Memory:</b>'),
                'Drives:': self.tr('<b>Drives:</b>'),
                'Network:': self.tr('<b>Network:</b>'),
                'Info:': self.tr('<b>Info:</b>'),
                'Machine:': self.tr('<b>Machine:</b>'),
                'Battery:': self.tr('<b>Battery:</b>'),
                'Processes:': self.tr('<b>Processes:</b>'),
                'Audio:': self.tr('<b>Audio:</b>'),
                'Sensors:': self.tr('<b>Sensors:</b>'),
                'Graphics:': self.tr('<b>Graphics:</b>'),
                'Display:': self.tr('<b>Display:</b>'),
                'Bluetooth:': self.tr('<b>Bluetooth:</b>'),

                # Common terms with colon and formatting
                'speed:': self.tr('<b>speed:</b>'),
                'type:': self.tr('<b>type:</b>'),
                'size:': self.tr('<b>size:</b>'),
                'used:': self.tr('<b>Used:</b>'),
                'serial:': self.tr('<b>serial:</b>'),
                'driver:': self.tr('<b>driver:</b>'),
                'drivers:': self.tr('<b>drivers:</b>'),
                'version:': self.tr('<b>version:</b>'),
                'model:': self.tr('<b>model:</b>'),
                'device:': self.tr('<b>device:</b>'),
                'vendor:': self.tr('<b>vendor:</b>'),
                'partition:': self.tr('<b>Partition:</b>'),
                'swap:': self.tr('<b>Swap File:</b>'),

                # The same terms with capital letters
                'Type:': self.tr('<b>Type:</b>'),
                # 'Size:': self.tr('<b>Size:</b>'),
                'Used:': self.tr('<b>Used:</b>'),
                # 'Serial:': self.tr('<b>Serial Number:</b>'),
                'Version:': self.tr('<b>Version:</b>'),
                'Model:': self.tr('<b>Model:</b>'),
                'Device:': self.tr('<b>Device:</b>'),
                'Vendor:': self.tr('<b>Vendor:</b>'),
                'Partition:': self.tr('<b>Partition:</b>'),
                'Swap:': self.tr('<b>Swap:</b>'),

                # Common terms without formatting
                'menu': self.tr('Hardware'),
                'title': self.tr('Hardware Information'),
                'System': self.tr('System'),
                'Kernel': self.tr('Kernel'),
                'Desktop': self.tr('Desktop'),
                'Laptop': self.tr('Laptop'),
                'type': self.tr('Type'),
                'model': self.tr('Model'),
                # 'serial': self.tr('Serial Number'),
                'product:': self.tr('<b>product:</b>'),
                'charge:': self.tr('<b>charge:</b>'),
                'condition:': self.tr('<b>condition:</b>'),
                'core:': self.tr('<b>Core:</b>'),
                'cores:': self.tr('<b>Cores:</b>'),
                'cache': self.tr('Cache'),
                'avg:': self.tr('<b>Average:</b>'),
                'server:': self.tr('<b>server:</b>'),
                ' loaded:': self.tr('<b> Loaded:</b>'),
                'unloaded:': self.tr('<b>Unloaded</b>'),
                'resolution:': self.tr('<b>resolution:</b>'),
                'platforms:': self.tr('<b>platforms:</b>'),
                'renderer': self.tr('<b>renderer:</b>'),
                'surfaces': self.tr('<b>surfaces:</b>'),
                'state:': self.tr('<b>state:</b>'),
                'status:': self.tr('<b>status:</b>'),
                'active': self.tr('Active'),
                'with': self.tr('With'),
                'compositor': self.tr('Compositor'),
                'arch:': self.tr('<b>Architecture:</b>'),
                'bits:': self.tr('<b>Bits:</b>'),
                'Report:': self.tr('<b>Report:</b>'),
                'address:': self.tr('<b>address:</b>'),
                'bt-v:': self.tr('<b>bt-v:</b>'),
                'cpu:': self.tr('<b>cpu:</b>'),
                'mobo:': self.tr('<b>mobo:</b>'),

                ' ID:': ' <b>ID:</b>',
                'ID-1:': '<b>ID-1:</b>',
                'ID-2:': '<b>ID-2:</b>',
                'ID-3:': '<b>ID-3:</b>',
                'ID-4:': '<b>ID-4:</b>',
                'ID-5:': '<b>ID-5:</b>',
                'ID-6:': '<b>ID-6:</b>',
                'ID-7:': '<b>ID-7:</b>',
                'ID-8:': '<b>ID-8:</b>',

                'Device-1': '<b>Device-1</b>',
                'Device-2': '<b>Device-2</b>',
                'Device-3': '<b>Device-3</b>',
                'Device-4': '<b>Device-4</b>',

                'Server-1': '<b>Server-1</b>',
                'Server-2': '<b>Server-2</b>',
                'Server-3': '<b>Server-3</b>',
                'Server-4': '<b>Server-4</b>',

                'fan-1:': '<b>fan-1:</b>',
                'fan-2:': '<b>fan-2:</b>',
                'fan-3:': '<b>fan-3:</b>',
                'fan-4:': '<b>fan-4:</b>',
                'fan-5:': '<b>fan-5:</b>',
                'fan-6:': '<b>fan-6:</b>',

                ' v:': self.tr(' <b>v:</b>'),
                'compat-v:': self.tr('<b>compat-v:</b>'),
                'Distro:': self.tr('<b>Distro:</b>'),
                'Alert:': self.tr('<b>Alert:</b>'),
                'Mobo:': self.tr('<b>Mobo:</b>'),
                'date:': self.tr('<b>date:</b>'),
                'dri:': '<b>dri:</b>',
                'gpu:': '<b>gpu:</b>',
                'Speed (MHz):': self.tr('<b>Speed (MHz):</b>'),
                'min/max:': self.tr('<b>min/max:</b>'),
                'Local Storage:': self.tr('<b>Local Storage:</b>'),
                'total:': self.tr('<b>total:</b>'),
                'note:': self.tr('<b>note:</b>'),
                ' est.': self.tr(' est.'),
                'available:': self.tr('<b>available:</b>'),
                'fs:': self.tr('<b>fs:</b>'),
                'dev:': self.tr('<b>dev:</b>'),
                'Uptime:': self.tr('<b>Uptime:</b>'),
                'Client:': self.tr('<b>Client:</b>'),
                'Tools:': self.tr('<b>Tools:</b>'),
                'api:': '<b>api:</b>',
                'de:': '<b>de:</b>',
                'x11:': '<b>x11:</b>',

                'Host:': '<b>Host:</b>',
                'BIOS:': '<b>BIOS:</b>',
                'UEFI:': '<b>UEFI:</b>',
                'API:': '<b>API:</b>',
                'IF:': '<b>IF:</b>',
                'mac:': '<b>mac:</b>',
                'Shell:': '<b>Shell:</b>',
                'inxi:': '<b>inxi:</b>',

                # Units of measurement
                'KiB': self.tr('KiB'),
                'GiB': self.tr('GiB'),
                'MiB': self.tr('MiB'),
                'MHz': self.tr('MHz'),
                'Wh': self.tr('Wh'),

                'min': self.tr('Min'),
                'max': self.tr('Max'),
                ' up ': self.tr(' up '),
                ' down ': self.tr(' down '),

                'No swap data was found': self.tr('No swap data was found'),
            }

            # core numbers
            for i in range(1,33):
                key = f' {i}: '
                value = f' <b>{i}:</b> '
                # print(f'{key=}', '  ', f'{value=}')
                translations[key] = value


            # Заменяем термины на переведенные версии
            for key, value in enumerate(info):
                # print(key, "    ", value)
                # print(value)
                # if value in separators:
                #     info[key] = '<hr style="border: 1px solid #000000; margin: 10px 0;">' + value
                #     print(info[key])
                for eng, translated in translations.items():
                    value = value.replace(eng, translated)
                info[key] = value
                # print(info[key])

            # Форматируем вывод для HTML
            system_info = "<h3>" + self.tr("Hardware Information") + "</h3>"
            system_info = system_info + "<p>" + "</p><p>".join(info) + "</p>"

        except Exception as e:
            s = self.tr('Error getting system information')
            system_info = f"<p>{s}: {e}</p>"

        return system_info


class PluginHardware(plugins.Base):
    def __init__(self):
        super().__init__("hardware", 30)
        self.node = None

    def start(self, plist, pane):
        self.node = QStandardItem(self.tr("Hardware"))
        self.node.setData(self.getName())
        plist.appendRow([self.node])

        self.text_browser = QTextBrowser()
        # self.text_browser.setCurrentFont(QFont("Monospace Regular", 9))
        gsi = GetSystemInfo()
        self.text_browser.setHtml(gsi.get_system_info())
        self.text_browser.setOpenExternalLinks(False)
        pane.addWidget(self.text_browser)
