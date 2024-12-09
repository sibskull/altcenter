#!/usr/bin/python3

from PyQt5.QtWidgets import (QWidget, QVBoxLayout, QLabel, QGroupBox,
                            QGridLayout, QScrollArea, QTextBrowser)
from PyQt5.QtGui import QStandardItem, QFont, QTextDocument
from PyQt5.QtCore import Qt
from PyQt5.QtCore import QUrl

import locale, os

import plugins

# class UsefulWidget(QWidget):
#     def __init__(self):
#         super().__init__()
#         self.current_language = 'ru'
#         self.initUI()

#     def initUI(self):
#         # Основной layout
#         main_layout = QVBoxLayout()

#         # Создаем область прокрутки
#         scroll = QScrollArea()
#         scroll.setWidgetResizable(True)
#         scroll.setFrameShape(QScrollArea.NoFrame)

#         # Контейнер для содержимого
#         container = QWidget()
#         layout = QVBoxLayout(container)
#         layout.setSpacing(20)

#         # Определяем заголовки групп в зависимости от языка
#         group_titles = {
#             # 'en': {
#             'commands': self.tr("Useful Commands"),
#             'apps': self.tr("Recommended Applications"),
#             'tips': self.tr("Tips and Tricks")
#             # },
#             # 'ru': {
#             #     'commands': "Полезные команды",
#             #     'apps': "Рекомендуемые приложения",
#             #     'tips': "Советы и рекомендации"
#             # }
#         }

#         # Создаем группы
#         commands = QGroupBox(group_titles['commands'])
#         commands_grid = QGridLayout()
#         commands_grid.setSpacing(10)

#         apps = QGroupBox(group_titles['apps'])
#         apps_grid = QGridLayout()
#         apps_grid.setSpacing(10)

#         tips = QGroupBox(group_titles['tips'])
#         tips_grid = QGridLayout()
#         tips_grid.setSpacing(10)

#         # Наполняем информацией
#         self.fill_commands(commands_grid)
#         self.fill_apps(apps_grid)
#         self.fill_tips(tips_grid)

#         # Применяем стили
#         style = """
#             QGroupBox {
#                 font-weight: bold;
#                 border: 2px solid #CCCCCC;
#                 border-radius: 6px;
#                 margin-top: 6px;
#                 padding-top: 10px;
#             }
#             QGroupBox::title {
#                 subcontrol-origin: margin;
#                 left: 10px;
#                 padding: 0 3px;
#             }
#             QLabel {
#                 font-size: 14px;
#                 padding: 5px;
#             }
#             QLabel:hover {
#                 background-color: rgba(0, 0, 0, 0.1);
#                 border-radius: 4px;
#             }
#         """

#         commands.setStyleSheet(style)
#         apps.setStyleSheet(style)
#         tips.setStyleSheet(style)

#         # Устанавливаем layouts
#         commands.setLayout(commands_grid)
#         apps.setLayout(apps_grid)
#         tips.setLayout(tips_grid)

#         # Добавляем группы в layout
#         layout.addWidget(commands)
#         layout.addWidget(apps)
#         layout.addWidget(tips)
#         layout.addStretch()

#         # Устанавливаем контейнер в область прокрутки
#         scroll.setWidget(container)
#         main_layout.addWidget(scroll)

#         self.setLayout(main_layout)

#     def fill_commands(self, grid):
#         commands = {
#             # 'en': [
#             (self.tr("Superuser privileges"), "su -"),
#             (self.tr("System update"), "apt-get update"),
#             (self.tr("Package install"), "apt-get install package_name"),
#             (self.tr("System information"), "inxi -F"),
#             (self.tr("Disk usage"), "df -h")
#             # ],
#             # 'ru': [
#             #     ("🗂️ Права суперпользователя", "su -"),
#             #     ("🔍 Обновление системы", "apt-get update"),
#             #     ("📦 Установка пакета", "apt-get install package_name"),
#             #     ("💻 Информация о системе", "inxi -F"),
#             #     ("📊 Использование диска", "df -h")
#             # ]
#         }

#         row = 0
#         for title, command in commands:
#             label = QLabel(f"{title}: <code>{command}</code>")
#             label.setTextFormat(Qt.RichText)
#             label.setTextInteractionFlags(Qt.TextSelectableByMouse)
#             grid.addWidget(label, row, 0)
#             row += 1

#     def fill_apps(self, grid):
#         apps = {
#             # 'en': [
#             (self.tr("Graphics"), "GIMP, Inkscape, Krita"),
#             (self.tr("Audio"), "Audacity, VLC"),
#             (self.tr("Office"), "LibreOffice, OnlyOffice"),
#             (self.tr("Communication"), "Telegram, Element"),
#             (self.tr("Browsers"), "Firefox, Chromium")
#             # ],
#             # 'ru': [
#             #     ("🎨 Графика", "GIMP, Inkscape, Krita"),
#             #     ("🎵 Аудио", "Audacity, VLC"),
#             #     ("📝 Офис", "LibreOffice, OnlyOffice"),
#             #     ("💬 Общение", "Telegram, Element"),
#             #     ("🌐 Браузеры", "Firefox, Chromium")
#             # ]
#         }

#         row = 0
#         for category, app_list in apps:
#             label = QLabel(f"{category}: {app_list}")
#             label.setWordWrap(True)
#             label.setTextInteractionFlags(Qt.TextSelectableByMouse)
#             grid.addWidget(label, row, 0)
#             row += 1

#     def fill_tips(self, grid):
#         tips = {
#             # 'en': [
#             self.tr("Use Alt+F2 to quickly run applications"),
#             self.tr("Install additional applications through Software Center"),
#             self.tr("Use PortProton to run Windows games"),
#             self.tr("Regular system updates improve security"),
#             self.tr("Back up important data regularly"),
#             self.tr("Use strong passwords for better security")
#             # ],
#             # 'ru': [
#             #     "💡 Используйте Alt+F2 для быстрого запуска приложений",
#             #     "📦 Установка дополнительных программ доступна через Центр программ",
#             #     "🔄 Используйте PortProton для запуска Windows-игр",
#             #     "🔄 Регулярные обновления системы улучшают безопасность",
#             #     "💾 Регулярно делайте резервные копии важных данных",
#             #     "🔐 Используйте надёжные пароли для лучшей безопасности"
#             # ]
#         }

#         row = 0
#         for tip in tips:
#             label = QLabel(tip)
#             label.setWordWrap(True)
#             label.setTextInteractionFlags(Qt.TextSelectableByMouse)
#             grid.addWidget(label, row, 0)
#             row += 1

#     def update_language(self, language):
#         self.current_language = language
#         # Удаляем старый layout
#         if self.layout():
#             QWidget().setLayout(self.layout())
#         # Создаем новый интерфейс с обновленным языком
#         self.initUI()

class PluginUseful(plugins.Base):
    def __init__(self):
        super().__init__(50)
        self.node = None
        self.useful_widget = None

    # def start(self, plist, pane):
    #     self.node = QStandardItem(self.tr("Useful Information"))
    #     plist.appendRow([self.node])

    #     self.useful_widget = UsefulWidget()
    #     pane.addWidget(self.useful_widget)

    def start(self, plist, pane):
        self.node = QStandardItem(self.tr("Useful Information"))
        plist.appendRow([self.node])

        self.license_info = QTextBrowser()
        self.license_info.setCurrentFont(QFont("monospace", 9))
        self.index = pane.addWidget(self.license_info)

        current_file = os.path.abspath(__file__)
        current_dir = os.path.dirname(current_file)
        parent_dir = os.path.dirname(current_dir)
        file_name = 'useful_' + locale.getlocale()[0].split( '_' )[0] + '.md'
        file_path = os.path.join(parent_dir, 'translations', file_name)

        if os.path.isfile(file_path):
            url = QUrl(file_path)
            self.license_info.setSource(url, QTextDocument.ResourceType.MarkdownResource)
        else:
            file_path = os.path.join(parent_dir, 'translations', 'useful_en.md')
            if os.path.isfile(file_path):
                url = QUrl(file_path)
                self.license_info.setSource(url, QTextDocument.ResourceType.MarkdownResource)
            else:
                self.license_info.setHtml(f"File '{file_path}' not found.")
