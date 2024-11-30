#!/usr/bin/python3

import plugins
from PyQt5.QtWidgets import (QWidget, QVBoxLayout, QLabel, QGroupBox,
                            QGridLayout, QScrollArea, QPushButton)
from PyQt5.QtGui import QStandardItem, QIcon
from PyQt5.QtCore import Qt, QSize
import webbrowser  # Добавляем для открытия ссылок

class DocumentationWidget(QWidget):
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
        layout.setSpacing(20)  # Отступы между группами

        # Определяем заголовки групп в зависимости от языка
        group_titles = {
            #'en': {
            'main': self.tr("Main Resources"),
            'docs': self.tr("Documentation"),
            'support': self.tr("Support")
            #},
            # 'ru': {
            #     'main': "Основные ресурсы",
            #     'docs': "Документация",
            #     'support': "Поддержка"
            # }
        }

        # Группы
        main_resources = QGroupBox(group_titles['main'])
        main_grid = QGridLayout()
        main_grid.setSpacing(10)

        documentation = QGroupBox(group_titles['docs'])
        docs_grid = QGridLayout()
        docs_grid.setSpacing(10)

        support = QGroupBox(group_titles['support'])
        support_grid = QGridLayout()
        support_grid.setSpacing(10)

        # Определяем ссылки в зависимости от языка
        links = {
            "main": {
                "https://basealt.ru": (self.tr("Company Website"), "🏢"),
                "https://altlinux.org": (self.tr("ALT Linux Wiki Information Resource (RU)"), "🌐"),
                "https://packages.altlinux.org/en": (self.tr("Repositories"), "📦")
            },
            "docs": {
                "https://docs.altlinux.org": (self.tr("Product Documentation (RU)"), "📚"),
                "file:///usr/share/doc/indexhtml/documentation/ru-RU/index.html": (self.tr("User Manual"), "📖")
            },
            "support": {
                "https://basealt.ru/sr": (self.tr("Support Request (RU)"), "🔧"),
                "https://bugs.altlinux.org": (self.tr("Report a Bug (RU)"), "🐛"),
                "https://basealt.ru/en/product-feedback": (self.tr("Leave Feedback (RU)"), "📝")
            }
        }

        # Создаем и добавляем кнопки-ссылки в соответствующие группы
        current_links = links

        def create_button(url, text, icon):
            button = QPushButton(f"{icon} {text}")
            button.setCursor(Qt.PointingHandCursor)
            button.clicked.connect(lambda: webbrowser.open(url))
            button.setStyleSheet("""
                QPushButton {
                    text-align: left;
                    padding: 8px 12px;
                    border: 1px solid #2C2C2C;
                    border-radius: 4px;
                    color: white;
                    background-color: #3D3D3D;  /* тёмно-серый */
                    min-width: 200px;
                    min-height: 40px;
                }
                QPushButton:hover {
                    background-color: #4D4D4D;  /* серый чуть светлее при наведении */
                    border: 1px solid #2C2C2C;
                }
                QPushButton:pressed {
                    background-color: #2196F3;  /* синий при нажатии */
                    border: 1px solid #1976D2;
                }
            """)
            return button

        row = 0
        for url, (text, icon) in current_links["main"].items():
            button = create_button(url, text, icon)
            main_grid.addWidget(button, row, 0)
            row += 1

        row = 0
        for url, (text, icon) in current_links["docs"].items():
            button = create_button(url, text, icon)
            docs_grid.addWidget(button, row, 0)
            row += 1

        row = 0
        for url, (text, icon) in current_links["support"].items():
            button = create_button(url, text, icon)
            support_grid.addWidget(button, row, 0)
            row += 1

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
                background-color: #F5F5F5;
                border-radius: 4px;
            }
        """

        main_resources.setStyleSheet(style)
        documentation.setStyleSheet(style)
        support.setStyleSheet(style)

        # Устанавливаем layouts
        main_resources.setLayout(main_grid)
        documentation.setLayout(docs_grid)
        support.setLayout(support_grid)

        # Добавляем группы в layout
        layout.addWidget(main_resources)
        layout.addWidget(documentation)
        layout.addWidget(support)
        layout.addStretch()

        # Устанавливаем контейнер в область прокрутки
        scroll.setWidget(container)
        main_layout.addWidget(scroll)

        self.setLayout(main_layout)

    def update_language(self, language):
        self.current_language = language
        # Удаляем старый layout
        if self.layout():
            QWidget().setLayout(self.layout())
        # Создаем новый интерфейс с обновленным языком
        self.initUI()

class PluginDocumentation(plugins.Base):
    def __init__(self):
        super().__init__()
        self.node = None
        self.documentation_widget = None
        self.current_language = 'ru'

    def start(self, plist, pane):
        self.node = QStandardItem(self.tr("Documentation"))
        plist.appendRow([self.node])

        self.documentation_widget = DocumentationWidget()
        pane.addWidget(self.documentation_widget)

    # def update_language(self, language):
    #     menu_titles = {
    #         'en': "Documentation",
    #         'ru': "Документация"
    #     }
    #     self.node.setText(menu_titles[language])
    #     if self.documentation_widget:
    #         self.documentation_widget.update_language(language)
