#!/usr/bin/python3

import plugins
from PyQt5.QtWidgets import (QWidget, QVBoxLayout, QLabel, QGroupBox, 
                            QGridLayout, QScrollArea)
from PyQt5.QtGui import QStandardItem
from PyQt5.QtCore import Qt

class UsefulWidget(QWidget):
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
                'commands': "Useful Commands",
                'apps': "Recommended Applications",
                'tips': "Tips and Tricks"
            },
            'ru': {
                'commands': "Полезные команды",
                'apps': "Рекомендуемые приложения",
                'tips': "Советы и рекомендации"
            }
        }
        
        # Создаем группы
        commands = QGroupBox(group_titles[self.current_language]['commands'])
        commands_grid = QGridLayout()
        commands_grid.setSpacing(10)
        
        apps = QGroupBox(group_titles[self.current_language]['apps'])
        apps_grid = QGridLayout()
        apps_grid.setSpacing(10)
        
        tips = QGroupBox(group_titles[self.current_language]['tips'])
        tips_grid = QGridLayout()
        tips_grid.setSpacing(10)
        
        # Наполняем информацией
        self.fill_commands(commands_grid)
        self.fill_apps(apps_grid)
        self.fill_tips(tips_grid)
        
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
            }
            QLabel:hover {
                background-color: rgba(0, 0, 0, 0.1);
                border-radius: 4px;
            }
        """
        
        commands.setStyleSheet(style)
        apps.setStyleSheet(style)
        tips.setStyleSheet(style)
        
        # Устанавливаем layouts
        commands.setLayout(commands_grid)
        apps.setLayout(apps_grid)
        tips.setLayout(tips_grid)
        
        # Добавляем группы в layout
        layout.addWidget(commands)
        layout.addWidget(apps)
        layout.addWidget(tips)
        layout.addStretch()
        
        # Устанавливаем контейнер в область прокрутки
        scroll.setWidget(container)
        main_layout.addWidget(scroll)
        
        self.setLayout(main_layout)

    def fill_commands(self, grid):
        commands = {
            'en': [
                ("🗂️ Superuser privileges", "su -"),
                ("🔍 System update", "apt-get update"),
                ("📦 Package install", "apt-get install package_name"),
                ("💻 System information", "inxi -F"),
                ("📊 Disk usage", "df -h")
            ],
            'ru': [
                ("🗂️ Права суперпользователя", "su -"),
                ("🔍 Обновление системы", "apt-get update"),
                ("📦 Установка пакета", "apt-get install package_name"),
                ("💻 Информация о системе", "inxi -F"),
                ("📊 Использование диска", "df -h")
            ]
        }
        
        row = 0
        for title, command in commands[self.current_language]:
            label = QLabel(f"{title}: <code>{command}</code>")
            label.setTextFormat(Qt.RichText)
            grid.addWidget(label, row, 0)
            row += 1

    def fill_apps(self, grid):
        apps = {
            'en': [
                ("🎨 Graphics", "GIMP, Inkscape, Krita"),
                ("🎵 Audio", "Audacity, VLC"),
                ("📝 Office", "LibreOffice, OnlyOffice"),
                ("💬 Communication", "Telegram, Element"),
                ("🌐 Browsers", "Firefox, Chromium")
            ],
            'ru': [
                ("🎨 Графика", "GIMP, Inkscape, Krita"),
                ("🎵 Аудио", "Audacity, VLC"),
                ("📝 Офис", "LibreOffice, OnlyOffice"),
                ("💬 Общение", "Telegram, Element"),
                ("🌐 Браузеры", "Firefox, Chromium")
            ]
        }
        
        row = 0
        for category, app_list in apps[self.current_language]:
            label = QLabel(f"{category}: {app_list}")
            label.setWordWrap(True)
            grid.addWidget(label, row, 0)
            row += 1

    def fill_tips(self, grid):
        tips = {
            'en': [
                "💡 Use Alt+F2 to quickly run applications",
                "📦 Install additional applications through Software Center",
                "🔄 Use PortProton to run Windows games",
                "🔄 Regular system updates improve security",
                "💾 Back up important data regularly",
                "🔐 Use strong passwords for better security"
            ],
            'ru': [
                "💡 Используйте Alt+F2 для быстрого запуска приложений",
                "📦 Установка дополнительных программ доступна через Центр программ",
                "🔄 Используйте PortProton для запуска Windows-игр",
                "🔄 Регулярные обновления системы улучшают безопасность",
                "💾 Регулярно делайте резервные копии важных данных",
                "🔐 Используйте надёжные пароли для лучшей безопасности"
            ]
        }
        
        row = 0
        for tip in tips[self.current_language]:
            label = QLabel(tip)
            label.setWordWrap(True)
            grid.addWidget(label, row, 0)
            row += 1

    def update_language(self, language):
        self.current_language = language
        # Удаляем старый layout
        if self.layout():
            QWidget().setLayout(self.layout())
        # Создаем новый интерфейс с обновленным языком
        self.initUI()

class PluginUseful(plugins.Base):
    def __init__(self):
        self.node = None
        self.useful_widget = None
        self.current_language = 'ru'

    def start(self, plist, pane):
        self.node = QStandardItem("Useful Information")
        plist.appendRow([self.node])

        self.useful_widget = UsefulWidget()
        index = pane.addWidget(self.useful_widget)

    def update_language(self, language):
        menu_titles = {
            'en': "Useful Information",
            'ru': "Полезная информация"
        }
        self.node.setText(menu_titles[language])
        if self.useful_widget:
            self.useful_widget.update_language(language) 
