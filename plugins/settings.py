#!/usr/bin/python3

import plugins
from PyQt5.QtWidgets import (QWidget, QVBoxLayout, QLabel, QGroupBox,
                            QGridLayout, QScrollArea, QCheckBox,
                            QComboBox, QPushButton)
from PyQt5.QtGui import QStandardItem, QIcon
from PyQt5.QtCore import Qt, QSize
import json
import os
import subprocess

class SettingsWidget(QWidget):
    def __init__(self):
        super().__init__()
        self.current_language = 'ru'
        # Инициализируем виджеты
        self.init_widgets()
        self.initUI()

    def init_widgets(self):
        """Инициализация всех виджетов"""
        # Основные настройки
        self.darkModeCheck = QCheckBox()


        # Настройки обновлений
        self.autoUpdateCheck = QCheckBox()
        self.updateFreqCombo = QComboBox()
        update_frequencies = [self.tr('Daily'), self.tr('Weekly'), self.tr('Monthly')]
            # 'ru': ['Ежедневно', 'Еженедельно', 'Ежемесячно'],
            # 'en':

        self.updateFreqCombo.addItems(update_frequencies)

        self.notifyUpdatesCheck = QCheckBox()

        # Кнопка сохранения
        button_text = self.tr("Save Settings")
        self.saveButton = QPushButton(f"💾 {button_text}")
        self.saveButton.clicked.connect(self.saveSettings)

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

        # Определяем заголовки групп
        group_titles = {
            # 'en': {
            'general': self.tr("General Settings"),
            'updates': self.tr("Updates"),
            'launch': self.tr("Advanced Settings")
            # },
            # 'ru': {
            #     'general': "Общие настройки",
            #     'updates': "Обновления",
            #     'launch': "Расширенные настройки"
            # }
        }

        # Группа основных настроек
        general = QGroupBox(group_titles['general'])
        general_grid = QGridLayout()
        general_grid.setSpacing(10)

        # Определяем метки для элементов
        labels = {
            # 'en': {
            'dark_mode': self.tr("🌙 Dark Theme"),
            'auto_update': self.tr("🔄 Enable Auto-update"),
            'update_freq': self.tr("⏰ Update Frequency"),
            'notify': self.tr("🔔 Notify About Updates")
            # },
            # 'ru': {
            #     'dark_mode': "🌙 Тёмная тема",
            #     'language': "🌐 Язык",
            #     'auto_update': "🔄 Включить автообновление",
            #     'update_freq': "⏰ Частота обновлений",
            #     'notify': "🔔 Уведомлять об обновлениях"
            # }
        }

        # Добавляем элементы в general_grid
        general_grid.addWidget(QLabel(labels['dark_mode']), 0, 0)
        general_grid.addWidget(self.darkModeCheck, 0, 1)

        general.setLayout(general_grid)

        # Группа обновлений
        updates = QGroupBox(group_titles['updates'])
        updates_grid = QGridLayout()
        updates_grid.setSpacing(10)

        # Добавляем элементы в updates_grid
        updates_grid.addWidget(QLabel(labels['auto_update']), 0, 0)
        updates_grid.addWidget(self.autoUpdateCheck, 0, 1)
        updates_grid.addWidget(QLabel(labels['update_freq']), 1, 0)
        updates_grid.addWidget(self.updateFreqCombo, 1, 1)
        updates_grid.addWidget(QLabel(labels['notify']), 2, 0)
        updates_grid.addWidget(self.notifyUpdatesCheck, 2, 1)

        updates.setLayout(updates_grid)

        # Добавляем новую группу для кнопок запуска
        launch = QGroupBox(group_titles['launch'])
        launch_grid = QGridLayout()
        launch_grid.setSpacing(10)

        # Определяем приложения для запуска
        apps = {
            # 'ru': [
            #     {
            #         'icon': 'center.png',
            #         'name': 'Центр управления системой',
            #         'command': 'acc',
            #         'tooltip': 'Управление учётными записями, системные журналы, обновлнение ядра.'
            #     },
            #     {
            #         'icon': 'system.png',
            #         'name': 'Параметры системы',
            #         'command': 'systemsettings5',
            #         'tooltip': 'Общие настройки: энергосбережение, сеть, дата, поведение рабочей среды.'
            #     },
            #     {
            #         'icon': 'info.png',
            #         'name': 'О системе',
            #         'command': 'kinfocenter',
            #         'tooltip': 'Информация о установленной системе.'
            #     },
            #     {
            #         'icon': 'preferences-desktop-display',  # Используем системную иконку
            #         'name': 'Настройки экрана',
            #         'command': 'kcmshell5 kcm_kscreen',
            #         'tooltip': 'Изменение настроек экрана.'
            #     }
            # ],
            'en':[
                {
                    'icon': 'center.png',
                    'name': self.tr('System Control Center'),
                    'command': 'acc',
                    'tooltip': self.tr('User account management, system logs, kernel updates.')
                },
                {
                    'icon': 'system.png',
                    'name': self.tr('System Settings'),
                    'command': 'systemsettings5',
                    'tooltip': self.tr('General settings: power management, network, date, workspace behavior.')
                },
                {
                    'icon': 'info.png',
                    'name': self.tr('About System'),
                    'command': 'kinfocenter',
                    'tooltip': self.tr('Information about installed system.')
                },
                {
                    'icon': 'preferences-desktop-display',
                    'name': self.tr('Display Settings'),
                    'command': 'kcmshell5 kcm_kscreen',
                    'tooltip': self.tr('Change display settings.')
                }
            ]
        }

        # Создаем кнопки для каждого приложения
        for i, app in enumerate(apps['en']):
            button = QPushButton()

            # Устанавливаем иконку
            if app['icon'].endswith('.png'):
                icon_path = os.path.join('res', app['icon'])
                if os.path.exists(icon_path):
                    button.setIcon(QIcon(icon_path))
            else:
                button.setIcon(QIcon.fromTheme(app['icon']))

            button.setIconSize(QSize(32, 32))
            button.setText(app['name'])
            button.setToolTip(app['tooltip'])
            button.clicked.connect(lambda checked, cmd=app['command']: self.launch_app(cmd))

            # Устанавливаем стиль для кнопки
            button.setStyleSheet("""
                QPushButton {
                    text-align: left;
                    padding: 5px 10px;
                    border: 1px solid #2C2C2C;
                    border-radius: 4px;
                    min-width: 200px;
                    min-height: 40px;
                    color: white;  /* Белый цвет текста */
                    background-color: #3D3D3D;  /* Тёмно-серый фон */
                }
                QPushButton:hover {
                    background-color: #4D4D4D;  /* Чуть светлее при наведении */
                    color: white;
                    border: 1px solid #2C2C2C;
                }
                QPushButton:pressed {
                    background-color: #2196F3;  /* Синий при нажатии */
                    color: white;
                    border: 1px solid #1976D2;
                }
            """)

            launch_grid.addWidget(button, i // 2, i % 2)

        launch.setLayout(launch_grid)

        # Применем стили
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
            QPushButton {
                text-align: left;
                padding: 5px 10px;
                border: 1px solid #2C2C2C;
                border-radius: 4px;
                color: white;
                background-color: #3D3D3D;
            }
            QPushButton:hover {
                background-color: #4D4D4D;
                border: 1px solid #2C2C2C;
            }
            QPushButton:checked {
                background-color: #2196F3;  /* Оставляем текущий синий цвет для активной кнопки */
                border: 1px solid #1976D2;
            }
            QPushButton:pressed {
                background-color: #2196F3;
                border: 1px solid #1976D2;
            }
        """

        general.setStyleSheet(style)
        updates.setStyleSheet(style)
        launch.setStyleSheet(style)
        self.saveButton.setStyleSheet(style)
        self.saveButton.setObjectName("saveButton")

        # Добавляем группы в layout
        layout.addWidget(general)
        layout.addWidget(updates)
        layout.addWidget(self.saveButton)
        layout.addStretch()
        layout.addWidget(launch)

        # Устанавливаем контейнер в область прокрутки
        scroll.setWidget(container)
        main_layout.addWidget(scroll)

        self.setLayout(main_layout)

        # Загружаем сохраненные настройки
        self.loadSettings()

    def loadSettings(self):
        """Загрузка настроек из файла"""
        try:
            if os.path.exists('settings.json'):
                with open('settings.json', 'r') as f:
                    settings = json.load(f)
                    self.darkModeCheck.setChecked(settings.get('dark_mode', False))
                    self.autoUpdateCheck.setChecked(settings.get('auto_update', True))
                    self.updateFreqCombo.setCurrentText(settings.get('update_frequency', 'Еженедельно'))
                    self.notifyUpdatesCheck.setChecked(settings.get('notify_updates', True))
        except Exception as e:
            print(f"Error loading settings: {e}")

    def saveSettings(self):
        """Сохранение настроек в файл"""
        try:
            settings = {
                'dark_mode': self.darkModeCheck.isChecked(),
                'auto_update': self.autoUpdateCheck.isChecked(),
                'update_frequency': self.updateFreqCombo.currentText(),
                'notify_updates': self.notifyUpdatesCheck.isChecked()
            }

            with open('settings.json', 'w') as f:
                json.dump(settings, f, indent=4)
        except Exception as e:
            print(f"Error saving settings: {e}")

    def update_language(self, language):
        """Обновление языка итерфейса"""
        self.current_language = language
        # Обновляем интерфейс
        if self.layout():
            QWidget().setLayout(self.layout())
        self.init_widgets()
        self.initUI()

    def launch_app(self, command):
        """Запуск приложения"""
        try:
            subprocess.Popen(command.split())
        except Exception as e:
            print(f"Error launching application: {e}")

class PluginSettings(plugins.Base):
    def __init__(self):
        super().__init__(40)
        self.node = None
        self.settings_widget = None

    def start(self, plist, pane):
        self.node = QStandardItem(self.tr("Settings"))
        plist.appendRow([self.node])

        self.settings_widget = SettingsWidget()
        index = pane.addWidget(self.settings_widget)
