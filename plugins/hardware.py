#!/usr/bin/python3

import plugins
from PyQt5.QtWidgets import (QWidget, QVBoxLayout, QLabel, QGroupBox,
                            QGridLayout, QScrollArea, QTextBrowser, QFrame)
from PyQt5.QtGui import QStandardItem
from PyQt5.QtCore import Qt
import subprocess
import re

class HardwareWidget(QWidget):
    def __init__(self):
        super().__init__()
        self.current_language = 'ru'
        self.initUI()

    def initUI(self):
        # Основной layout
        main_layout = QVBoxLayout()

        # Создаем область прокрутки
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setFrameShape(QScrollArea.NoFrame)

        # Контейнер для содержимого
        container = QWidget()
        layout = QVBoxLayout(container)
        layout.setSpacing(20)

        # Определяем заголовки групп в зависимости от языка
        group_titles = {
            # 'en': {
            'about': self.tr("Hardware Information")
            # },
            # 'ru': {
            #     'about': "Информация об оборудовании"
            # }
        }

        # Группа информации о системе
        about_group = QGroupBox(group_titles['about'])
        about_grid = QGridLayout()
        about_grid.setSpacing(10)

        # Получаем информацию о системе через inxi -F
        try:
            system_info = subprocess.check_output(
                "inxi -F",
                shell=True,
                text=True
            )
            # Очищаем от специальных символов
            system_info = re.sub(r'', '', system_info)
            system_info = re.sub(r'12', '', system_info)

            # Расширенный список терминов для разделителей
            separators = [
                self.tr('Info:'),
                self.tr('Drives:'),
                self.tr('Bluetooth:'),
                self.tr('Graphics:'),
                self.tr('CPU:'),
                self.tr('Battery:'),
                self.tr('Machine:'),
                self.tr('Audio:'),
                self.tr('Network:'),
                self.tr('Sensors:'),
                self.tr('Swap:')
            ]


            # Добавляем белую разделительную линию
            for separator in separators:
                system_info = system_info.replace(separator, '<hr style="border: 1px solid #FFFFFF; margin: 10px 0;">' + separator)

            # Словари переводов для разных языков
            translations = {
                'en': {
                    # Special terms
                    'System Temperatures': self.tr('System Temperatures'),
                    'Fun speeds': self.tr('Fun speeds'),
                    'N/A': self.tr('N/A'),

                    # Units of measurement
                    'GiB': self.tr('GiB'),
                    'MiB': self.tr('MiB'),
                    'MHz': self.tr('MHz'),
                    'Wh': self.tr('Wh'),

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
                    'speed:': self.tr('<b>Speed:</b>'),
                    'type:': self.tr('<b>Type:</b>'),
                    'size:': self.tr('<b>Size:</b>'),
                    'used:': self.tr('<b>Used:</b>'),
                    'serial:': self.tr('<b>Serial Number:</b>'),
                    'driver:': self.tr('<b>Driver:</b>'),
                    'version:': self.tr('<b>Version:</b>'),
                    'model:': self.tr('<b>Model:</b>'),
                    'device:': self.tr('<b>Device:</b>'),
                    'vendor:': self.tr('<b>Vendor:</b>'),
                    'partition:': self.tr('<b>Partition:</b>'),
                    'swap:': self.tr('<b>Swap File:</b>'),

                    # The same terms with capital letters
                    'Speed:': self.tr('<b>Speed:</b>'),
                    'Type:': self.tr('<b>Type:</b>'),
                    'Size:': self.tr('<b>Size:</b>'),
                    'Used:': self.tr('<b>Used:</b>'),
                    'Serial:': self.tr('<b>Serial Number:</b>'),
                    'Driver:': self.tr('<b>Driver:</b>'),
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
                    'serial': self.tr('Serial Number'),
                    'product': self.tr('Product'),
                    'charge': self.tr('Charge'),
                    'condition': self.tr('Condition'),
                    'core': self.tr('Core'),
                    'cores': self.tr('Cores'),
                    'cache': self.tr('Cache'),
                    'speed': self.tr('Speed'),
                    'min': self.tr('Min'),
                    'max': self.tr('Max'),
                    'avg': self.tr('Average'),
                    'device': self.tr('Device'),
                    'driver': self.tr('Driver'),
                    'server': self.tr('Server'),
                    'loaded': self.tr('Loaded'),
                    'unloaded': self.tr('Unloaded'),
                    'resolution': self.tr('Resolution'),
                    'vendor': self.tr('Vendor'),
                    'renderer': self.tr('Renderer'),
                    'surfaces': self.tr('Surfaces'),
                    'status': self.tr('Status'),
                    'active': self.tr('Active'),
                    'with': self.tr('With'),
                    'compositor': self.tr('Compositor'),
                    'arch': self.tr('Architecture'),
                    'bits': self.tr('Bits')
                }
            }


            # Используем переводы в зависимости от текущего языка
            current_translations = translations['en']

            # Заменяем термины на переведенные версии
            for eng, translated in current_translations.items():
                system_info = system_info.replace(eng, translated)

            # Форматируем вывод для HTML
            system_info = "<p>" + system_info.replace("\n", "</p><p>") + "</p>"

        except Exception as e:
            system_info = f"<p>{'Error getting system information' if self.current_language == 'en' else 'Ошибка получения информации о системе'}: {e}</p>"

        # Создаем и добавляем текст в grid с сохранением HTML-форматирования
        label = QLabel()
        label.setWordWrap(True)
        label.setTextFormat(Qt.RichText)
        label.setOpenExternalLinks(False)
        label.setText(system_info)
        about_grid.addWidget(label, 0, 0)

        # Применяем стили
        style = """
            QGroupBox {
                font-weight: bold;
                border: 2px solid #CCCCCC;
                border-radius: 6px;
                margin-top: 6px;
                padding-top: 10px;
            }
            QGroupBox::title {
                subcontrol-origin: margin;
                left: 10px;
                padding: 0 3px;
            }
            QLabel {
                font-size: 14px;
                padding: 5px;
                line-height: 1.5;
            }
        """

        about_group.setStyleSheet(style)

        # Устанавливаем layout
        about_group.setLayout(about_grid)

        # Добавляем группу в layout
        layout.addWidget(about_group)
        layout.addStretch()

        # Устанавливаем контейнер в область прокрутки
        scroll.setWidget(container)
        main_layout.addWidget(scroll)

        self.setLayout(main_layout)

    def update_language(self, language):
        self.current_language = language
        if self.layout():
            QWidget().setLayout(self.layout())
        self.initUI()
# Убрать новые переводы
    def translate_hardware_info(self, text, language='ru'):
        if language == 'ru':
            translations = {
            }

    def retranslateUi(self):
        """Update interface language"""
        titles = {
            'en': {
            }
        }
        return titles[self.current_language]

class PluginHardware(plugins.Base):
    def __init__(self):
        super().__init__(30)
        self.name = "hardware"
        self.node = None
        self.hardware_widget = None
        self.current_language = 'ru'
        self.menu_titles = {
            'en': {
                'menu': self.tr("Hardware"),
                'system': self.tr("System"),
                'computer': self.tr("Computer"),
                'battery': self.tr("Battery"),
                'CPU': self.tr("Processor"),
                'graphics': self.tr("Graphics"),
                'audio': self.tr("Audio"),
                'kernel': self.tr("Kernel"),
                'arch': self.tr("arch"),
                'bits': self.tr("bits"),
                'desktop': self.tr("Desktop"),
                'type': self.tr("Type"),
                'laptop': self.tr("Laptop"),
                'product': self.tr("product"),
                'model': self.tr("model"),
                'serial': self.tr("serial"),
                'date': self.tr("date"),
                'charge': self.tr("charge"),
                'condition': self.tr("condition"),
                'Wh': self.tr("Wh"),
                'info': self.tr("Info"),
                'core': self.tr("core"),
                'cores': self.tr("cores"),
                'cache': self.tr("cache"),
                'speed': self.tr("Speed"),
                'min': self.tr("min"),
                'max': self.tr("max"),
                'avg': self.tr("avg"),
                'device': self.tr("Device"),
                'driver': self.tr("driver"),
                'server': self.tr("server"),
                'with': self.tr("with"),
                'compositor': self.tr("compositor"),
                'loaded': self.tr("loaded"),
                'unloaded': self.tr("unloaded"),
                'resolution': self.tr("resolution"),
                'vendor': self.tr("vendor"),
                'renderer': self.tr("renderer"),
                'surfaces': self.tr("surfaces"),
                'status': self.tr("status"),
                'active': self.tr("active"),
                'GiB': self.tr("GiB"),
                'MiB': self.tr("MiB"),
                'MHz': self.tr("MHz")
            }
            # 'ru': {
            #     'menu': "Оборудование",
            #     'system': "Система",
            #     'computer': "Компьютер",
            #     'battery': "Батарея",
            #     'processor': "Процессор",
            #     'graphics': "Графика",
            #     'audio': "Аудио",
            #     'kernel': "Ядро",
            #     'arch': "архитектура",
            #     'bits': "бит",
            #     'desktop': "Рабочий стол",
            #     'type': "Тип",
            #     'laptop': "Ноутбук",
            #     'product': "продукт",
            #     'model': "модель",
            #     'serial': "серийный номер",
            #     'charge': "заряд",
            #     'condition': "состояние",
            #     'Wh': "Вт⋅ч",
            #     'info': "Информация",
            #     'core': "ядро",
            #     'cores': "ядер",
            #     'cache': "кэш",
            #     'speed': "Частота",
            #     'min': "мин",
            #     'max': "макс",
            #     'avg': "средняя",
            #     'device': "Устройство",
            #     'driver': "драйвер",
            #     'server': "сервер",
            #     'with': "с",
            #     'compositor': "композитор",
            #     'loaded': "загружен",
            #     'unloaded': "выгружено",
            #     'resolution': "разрешение",
            #     'vendor': "производитель",
            #     'renderer': "рендерер",
            #     'surfaces': "поверхности",
            #     'status': "статус",
            #     'active': "активен",
            #     'GiB': "ГБ",
            #     'MiB': "МБ",
            #     'MHz': "МГц"
            # }
        }

    def start(self, plist, pane):
        self.node = QStandardItem(self.tr("Hardware"))
        self.node.setData(self.name)
        plist.appendRow([self.node])

        self.hardware_widget = HardwareWidget()
        pane.addWidget(self.hardware_widget)

    # def update_language(self, language):
    #     self.current_language = language
    #     menu_titles = {
    #         'en': "Hardware",
    #         'ru': "Оборудование"
    #     }
    #     self.node.setText(menu_titles[language])
    #     if self.hardware_widget:
    #         self.hardware_widget.update_language(language)

    def get_hardware_info(self):
        info = subprocess.check_output(['inxi', '-F', '--width', '80'], text=True)


        for key, value in self.menu_titles.items():
            info = info.replace(self.menu_titles['en'][key], value)

        return info
