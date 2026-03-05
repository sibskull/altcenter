#!/usr/bin/python3

import plugins
from PyQt5.QtWidgets import (QWidget, QVBoxLayout, QLabel, QGroupBox,
                            QGridLayout, QScrollArea, QCheckBox,
                            QComboBox, QPushButton, QStackedWidget)
from PyQt5.QtGui import QStandardItem, QStandardItemModel, QIcon
from PyQt5.QtCore import Qt, QSize, QProcess

import json
import os
import subprocess
import re

import my_utils

de_settings = { "KDE": "systemsettings",
                "GNOME": "gnome-control-center",
                "MATE": "mate-control-center",
                "XFCE": "xfce4-settings-manager",
              }

class SettingsWidget(QWidget):
    def __init__(self):
        super().__init__()
        self.current_language = 'ru'
        self.is_expert_mode = False
        # Инициализируем виджеты
        self.init_widgets()
        self.initUI()

    def set_expert_mode(self, enabled: bool):
        self.is_expert_mode = bool(enabled)

        if hasattr(self, 'applications_btn') and self.applications_btn is not None:
            self.applications_btn.setVisible(self.is_expert_mode)

        if hasattr(self, 'third_party_btn') and self.third_party_btn is not None:
            self.third_party_btn.setVisible(self.is_expert_mode)

        if hasattr(self, 'system_center_btn') and self.system_center_btn is not None:
            self.system_center_btn.setVisible(self.is_expert_mode)

    def init_widgets(self):
        """Инициализация всех виджетов"""
        # Основные настройки


        # Настройки обновлений
        self.autoUpdateCheck = QCheckBox()
        self.updateFreqCombo = QComboBox()
        update_frequencies = [self.tr('Daily'), self.tr('Weekly'), self.tr('Monthly')]
            # 'ru': ['Ежедневно', 'Еженедельно', 'Ежемесячно'],
            # 'en':

        self.updateFreqCombo.addItems(update_frequencies)

        self.notifyUpdatesCheck = QCheckBox()

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
            'updates': self.tr("Updates"),
            'launch': self.tr("Advanced Settings")
            # },
            # 'ru': {
            #     'general': "Общие настройки",
            #     'updates': "Обновления",
            #     'launch': "Расширенные настройки"
            # }
        }
        # Определяем метки для элементов
        labels = {
            # 'en': {
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
                    'icon': 'preferences',
                    'name': self.tr('User Settings'),
                    'command': '',
                    'tooltip': self.tr('General settings: power management, network, date, workspace behavior')
                },
                {
                    'icon': 'system',
                    'name': self.tr('System Control Center'),
                    'command': 'acc',
                    'tooltip': self.tr('User account management, system logs, kernel updates'),
                    'expert_only': True
                },
             ]
        }

        # Set correct user settings program for current desktop environment
        current_de = os.environ.get('XDG_CURRENT_DESKTOP', '')
        # Fix KDE on Wayland
        if current_de.startswith("KDE:"): current_de = "KDE"
        # Fix DE like Alt-GNOME:GNOME
        current_de = re.sub(r"^.*:", "", current_de)
        if current_de in de_settings:
            apps['en'][0]['command'] = de_settings[current_de]

        # Добавляем проверку системы для кнопки «Applications» (GNOME/KDE/MATE/XFCE)
        # Выбираем подходящий центр приложений в зависимости от DE и наличия пакетов
        has_discover = (
            my_utils.check_package_installed("plasma-discover") or
            my_utils.check_package_installed("plasma-discover-core") or
            my_utils.check_package_installed("plasma5-discover-core")
        )
        has_gs = my_utils.check_package_installed("gnome-software")

        app_center_cmd = ''
        if current_de == "GNOME" and has_gs:
            app_center_cmd = "gnome-software"
        elif current_de == "KDE" and has_discover:
            app_center_cmd = "plasma-discover"
        elif current_de in ("MATE", "XFCE"):
            if has_gs:
                app_center_cmd = "gnome-software"
            elif has_discover:
                app_center_cmd = "plasma-discover"
        else:
            if has_gs:
                app_center_cmd = "gnome-software"
            elif has_discover:
                app_center_cmd = "plasma-discover"

        if app_center_cmd:
            apps['en'].append({
                'icon': 'applications-system',
                'name': self.tr('Applications'),
                'command': app_center_cmd,
                'expert_only': True
            })

        self.applications_btn = None
        self.third_party_btn = None
        self.system_center_btn = None

        if my_utils.check_package_installed("appinstall"):
            apps['en'].append({
                'icon': 'system-software-install',
                'name': self.tr('Third party applications'),
                'command': 'appinstall',
                'expert_only': True
            })

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
            if 'tooltip' in app:
                button.setToolTip(app['tooltip'])

            if app.get('expert_only', False):
                if app.get('command') == 'acc':
                    self.system_center_btn = button
                elif app.get('name') == self.tr('Applications'):
                    self.applications_btn = button
                elif app.get('name') == self.tr('Third party applications'):
                    self.third_party_btn = button

            if app['command'] != '':
                button.clicked.connect(lambda checked, cmd=app['command']: self.launch_app(cmd))
            else:
                # Disable button
                button.setEnabled(False)

            # Устанавливаем стиль для кнопки
            button.setStyleSheet("""
                QPushButton {
                    text-align: left;
                    padding: 5px 10px;
                    min-width: 200px;
                    min-height: 40px;
                }
            """)

            launch_grid.addWidget(button, i // 2, i % 2)

        launch.setLayout(launch_grid)

        # Применем стили
        style = """
            QPushButton {
                text-align: left;
                padding: 5px 10px;
            }
        """
        updates.setStyleSheet(style)
        launch.setStyleSheet(style)

        # Добавляем группы в layout
        #layout.addWidget(updates)
        layout.addWidget(launch)
        layout.addStretch()

        # Устанавливаем контейнер в область прокрутки
        scroll.setWidget(container)
        main_layout.addWidget(scroll)

        self.setLayout(main_layout)

        # Загружаем сохраненные настройки
        self.loadSettings()

        self.set_expert_mode(self.is_expert_mode)

    def launch_apps(self):
        if my_utils.check_package_installed("gnome-software"):
            QProcess.startDetached("gnome-software")
        elif my_utils.check_package_installed("plasma-discover-core") or my_utils.check_package_installed("plasma5-discover-core"):
            QProcess.startDetached("plasma-discover")

    def launch_appinstall(self):
        QProcess.startDetached("appinstall")

    def loadSettings(self):
        """Загрузка настроек из файла"""
        try:
            if os.path.exists('settings.json'):
                with open('settings.json', 'r') as f:
                    settings = json.load(f)
                    self.autoUpdateCheck.setChecked(settings.get('auto_update', True))
                    self.updateFreqCombo.setCurrentText(settings.get('update_frequency', 'Еженедельно'))
                    self.notifyUpdatesCheck.setChecked(settings.get('notify_updates', True))
        except Exception as e:
            print(f"Error loading settings: {e}")

    def saveSettings(self):
        """Сохранение настроек в файл"""
        try:
            settings = {
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
    def __init__(self, plist: QStandardItemModel=None, pane: QStackedWidget = None):
        super().__init__("settings", 40, plist, pane)

        if self.plist != None and self.pane != None:
            self.node = QStandardItem(self.tr("Settings"))
            self.node.setData(self.name)
            self.plist.appendRow([self.node])
            self.pane.addWidget(QWidget())

    def _do_start(self, idx: int):
        main_window = self.pane.window()
        main_widget = SettingsWidget()

        try:
            if hasattr(main_window, '_expert_mode'):
                main_widget.set_expert_mode(bool(main_window._expert_mode))
        except Exception:
            pass

        self.pane.insertWidget(idx, main_widget)
