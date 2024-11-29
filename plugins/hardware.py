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
            'en': {
                'about': "Hardware Information"
            },
            'ru': {
                'about': "Информация об оборудовании"
            }
        }
        
        # Группа информации о системе
        about_group = QGroupBox(group_titles[self.current_language]['about'])
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
                'Info:', 'Информация:', 
                'Drives:', 'Накопители:', 
                'Bluetooth:', 
                'Graphics:', 'Графика:', 
                'CPU:', 'Процессор:', 
                'Battery:', 'Батарея:', 
                'Machine:', 'Компьютер:',
                'Audio:', 'Аудио:', 
                'Network:', 'Сеть:', 
                'Sensors:', 'Датчики:',
                'Swap:', 'Файл подкачки:'
            ]
            
            # Добавляем белую разделительную линию
            for separator in separators:
                system_info = system_info.replace(separator, '<hr style="border: 1px solid #FFFFFF; margin: 10px 0;">' + separator)
            
            # Словари переводов для разных языков
            translations = {
                'ru': {                    
                    # Специальные термины
                    'System Temperatures': 'Системная температура',
                    'Fun speeds': 'Скорость вращения вентилятора',
                    'N/A': 'не обнаружено',
                    
                    # Единицы измерения
                    'GiB': 'ГБ',
                    'MiB': 'МБ',
                    'MHz': 'МГц',
                    'Wh': 'Вт⋅ч',
                    # Заголовки с HTML-форматированием
                    'System:': '<b>Система:</b>',
                    'Kernel:': '<b>Ядро:</b>',
                    'Desktop:': '<b>Рабочий стол:</b>',
                    'CPU:': '<b>Процессор:</b>',
                    'GPU:': '<b>Видеокарта:</b>',
                    'Memory:': '<b>Оперативная память:</b>',
                    'Drives:': '<b>Накопители:</b>',
                    'Network:': '<b>Сеть:</b>',
                    'Info:': '<b>Информация:</b>',
                    'Machine:': '<b>Компьютер:</b>',
                    'Battery:': '<b>Батарея:</b>',
                    'Processes:': '<b>Процессы:</b>',
                    'Audio:': '<b>Аудио:</b>',
                    'Sensors:': '<b>Датчики:</b>',
                    'Graphics:': '<b>Графика:</b>',
                    'Display:': '<b>Дисплей:</b>',
                    'Bluetooth:': '<b>Bluetooth:</b>',
                    
                    # Общие термины с двоеточием и форматированием
                    'speed:': '<b>скорость:</b>',
                    'type:': '<b>тип:</b>',
                    'size:': '<b>размер:</b>',
                    'used:': '<b>использовано:</b>',
                    'serial:': '<b>серийный номер:</b>',
                    'driver:': '<b>драйвер:</b>',
                    'version:': '<b>версия:</b>',
                    'model:': '<b>модель:</b>',
                    'device:': '<b>устройство:</b>',
                    'vendor:': '<b>производитель:</b>',
                    'partition:': '<b>раздел:</b>',
                    'swap:': '<b>файл подкачки:</b>',
                    
                    # Те же термины с заглавной буквы
                    'Speed:': '<b>Скорость:</b>',
                    'Type:': '<b>Тип:</b>',
                    'Size:': '<b>Размер:</b>',
                    'Used:': '<b>Использовано:</b>',
                    'Serial:': '<b>Серийный номер:</b>',
                    'Driver:': '<b>Драйвер:</b>',
                    'Version:': '<b>Версия:</b>',
                    'Model:': '<b>Модель:</b>',
                    'Device:': '<b>Устройство:</b>',
                    'Vendor:': '<b>Производитель:</b>',
                    'Partition:': '<b>Раздел:</b>',
                    'Swap:': '<b>Файл подкачки:</b>',
                    
                    # Общие термины без форматирования
                    'menu': 'Оборудование',
                    'title': 'Информация об оборудовании',
                    'System': 'Система',
                    'Kernel': 'Ядро',
                    'Desktop': 'Рабочий стол',
                    'Laptop': 'Ноутбук',
                    'type': 'тип',
                    'model': 'модель',
                    'serial': 'серийный номер',
                    'product': 'продукт',
                    'charge': 'заряд',
                    'condition': 'состояние',
                    'core': 'ядро',
                    'cores': 'ядер',
                    'cache': 'кэш',
                    'speed': 'частота',
                    'min': 'мин',
                    'max': 'макс',
                    'avg': 'средняя',
                    'device': 'устройство',
                    'driver': 'драйвер',
                    'server': 'сервер',
                    'loaded': 'загружено',
                    'unloaded': 'выгружено',
                    'resolution': 'разрешение',
                    'vendor': 'производитель',
                    'renderer': 'рендерер',
                    'surfaces': 'поверхности',
                    'status': 'статус',
                    'active': 'активен',
                    'with': 'с',
                    'compositor': 'композитор',
                    'arch': 'архитектура',
                    'bits': 'бит',
                },
                'en': {
                    'System:': '<b>System:</b>',
                    'Kernel:': '<b>Kernel:</b>',
                    'Desktop:': '<b>Desktop:</b>',
                    'CPU:': '<b>CPU:</b>',
                    'GPU:': '<b>GPU:</b>',
                    'Memory:': '<b>Memory:</b>',
                    'Drives:': '<b>Drives:</b>',
                    'Network:': '<b>Network:</b>',
                    'Info:': '<b>Info:</b>',
                    'Machine:': '<b>Machine:</b>',
                    'Battery:': '<b>Battery:</b>',
                    'Processes:': '<b>Processes:</b>',
                    'Audio:': '<b>Audio:</b>',
                    'Sensors:': '<b>Sensors:</b>',
                    'Graphics:': '<b>Graphics:</b>',
                    'Display:': '<b>Display:</b>',
                    'Bluetooth:': '<b>Bluetooth:</b>',
                    'Partition:': '<b>Partition</b>',
                    'Swap:': '<b>Swap:</b>',
                    'Speed:': '<b>Speed:</b>',
                    'Type:': '<b>Type:</b>',
                    'Size:': '<b>Size:</b>',
                    'Used:': '<b>Used:</b>',
                    'Serial:': '<b>Serial:</b>',
                    'Driver:': '<b>Driver:</b>',
                    'Version:': '<b>Version:</b>',
                    'Model:': '<b>Model:</b>',
                    'Device:': '<b>Device:</b>',
                    'Vendor:': '<b>Vendor:</b>'
                }
            }
            
            # Используем переводы в зависимости от текущего языка
            current_translations = translations[self.current_language]
            
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
        self.node = None
        self.hardware_widget = None
        self.current_language = 'ru'
        self.menu_titles = {
            'en': {
                'menu': "Hardware",
                'system': "System",
                'computer': "Computer",
                'battery': "Battery",
                'processor': "Processor",
                'graphics': "Graphics",
                'audio': "Audio",
                'kernel': "Kernel",
                'arch': "arch",
                'bits': "bits",
                'desktop': "Desktop",
                'type': "Type",
                'laptop': "Laptop",
                'product': "product",
                'model': "model",
                'serial': "serial",
                'date': "date",
                'charge': "charge",
                'condition': "condition",
                'Wh': "Wh",
                'info': "Info",
                'core': "core",
                'cores': "cores",
                'cache': "cache",
                'speed': "Speed",
                'min': "min",
                'max': "max",
                'avg': "avg",
                'device': "Device",
                'driver': "driver",
                'server': "server",
                'with': "with",
                'compositor': "compositor",
                'loaded': "loaded",
                'unloaded': "unloaded",
                'resolution': "resolution",
                'vendor': "vendor",
                'renderer': "renderer",
                'surfaces': "surfaces",
                'status': "status",
                'active': "active",
                'GiB': "GiB",
                'MiB': "MiB",
                'MHz': "MHz"
            },
            'ru': {
                'menu': "Оборудование",
                'system': "Система",
                'computer': "Компьютер",
                'battery': "Баарея",
                'processor': "Процессор",
                'graphics': "Графика",
                'audio': "Аудио",
                'kernel': "Ядро",
                'arch': "архитектура",
                'bits': "бит",
                'desktop': "Рабочий стол",
                'type': "Тип",
                'laptop': "Ноутбук",
                'product': "продукт",
                'model': "модель",
                'serial': "серийный номер",
                'charge': "заряд",
                'condition': "состояние",
                'Wh': "Вт⋅ч",
                'info': "Информация",
                'core': "ядро",
                'cores': "ядер",
                'cache': "кэш",
                'speed': "Частота",
                'min': "мин",
                'max': "макс",
                'avg': "средняя",
                'device': "Устройство",
                'driver': "драйвер",
                'server': "сервер",
                'with': "с",
                'compositor': "композитор",
                'loaded': "загружен",
                'unloaded': "выгружено",
                'resolution': "разрешение",
                'vendor': "производитель",
                'renderer': "рендерер",
                'surfaces': "поверхности",
                'status': "статус",
                'active': "активен",
                'GiB': "ГБ",
                'MiB': "МБ",
                'MHz': "МГц"
            }
        }

    def start(self, plist, pane):
        self.node = QStandardItem("Оборудование")
        plist.appendRow([self.node])

        self.hardware_widget = HardwareWidget()
        index = pane.addWidget(self.hardware_widget)

    def update_language(self, language):
        self.current_language = language
        menu_titles = {
            'en': "Hardware",
            'ru': "Оборудование"
        }
        self.node.setText(menu_titles[language])
        if self.hardware_widget:
            self.hardware_widget.update_language(language)

    def get_hardware_info(self):
        info = subprocess.check_output(['inxi', '-F', '--width', '80'], text=True)

        if self.current_language == 'ru':
            for key, value in self.menu_titles[self.current_language].items():
                info = info.replace(self.menu_titles['en'][key], value)

        return info
