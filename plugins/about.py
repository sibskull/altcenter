#!/usr/bin/python3

from PyQt5.QtWidgets import (QApplication, QWidget,
                             QVBoxLayout, QLabel,
                             QGridLayout, QScrollArea,
                             QSpacerItem, QSizePolicy,
                             QMenu, QAction)
from PyQt5.QtGui import QStandardItem, QClipboard, QFont
from PyQt5.QtCore import Qt, QSize

import os
import sys
# import locale

import plugins
import my_utils

class AboutWidget(QWidget):
    def __init__(self, palette):
        super().__init__()
        self.palette = palette
        self.initUI()

    def translate_os_name(self, name:str) -> str:
        dictionary = {
            'ALT' : self.tr("ALT"),
            'ALT Education' : self.tr("ALT Education"),
            'ALT Workstation' : self.tr("ALT Workstation"),
            'ALT Workstation K' : self.tr("ALT Workstation K"),
            'ALT Regular' : self.tr("ALT Regular"),
            'Sisyphus' : self.tr("Sisyphus"),
            'ALT Server' : self.tr("ALT Server"),
            'ALT Virtualization Server' : self.tr("ALT Virtualization Server"),
            'ALT Starterkit' : self.tr("ALT Starterkit"),
        }

        if name in dictionary:
            name = dictionary[name]

        return name


    def initUI(self):
        self.setAutoFillBackground(True)
        self.setPalette(self.palette)

        # Основной лэйаут для окна
        main_layout = QVBoxLayout()

        # Создание QScrollArea
        scroll_area = QScrollArea(self)
        scroll_area.setWidgetResizable(True)  # Ресайз области прокрутки
        scroll_area.setFrameShape(QScrollArea.NoFrame)

        # Создание контейнера для виджетов внутри QScrollArea
        container = QWidget()
        # font = QFont('Sans', 11)
        # container.setFont(font)
        container_layout = QVBoxLayout(container)  # Внутренний лэйаут для контейнера
        container_layout.setSpacing(10)

        # Добавляем Spacer сверху (с помощью QSizePolicy.Expanding)
        top_spacer = QSpacerItem(20, 40, QSizePolicy.Minimum, QSizePolicy.Expanding)
        container_layout.addItem(top_spacer)

        # Создаем метки
        os_info = my_utils.parse_os_release()
        s = self.translate_os_name(os_info["MY_NAME"])
        os_name = "{}{}".format(s, os_info["MY_NAME_REST"])
        label1 = QLabel(os_name)
        label1.setAlignment(Qt.AlignCenter)
        label1.setWordWrap(True)
        label_font = container.font()
        label_font.setPointSize(int(label_font.pointSize()*1.25))
        label_font.setBold(True)
        label1.setFont(label_font)
        self.text = []
        self.text.append(os_name)

        label2 = QLabel('<a href="https://www.basealt.ru/">https://www.basealt.ru/</a>')
        label2.setAlignment(Qt.AlignCenter)
        label2.setOpenExternalLinks(True)
        self.text.append('https://www.basealt.ru/')

        # Добавляем метки в контейнер
        container_layout.addWidget(label1)
        container_layout.addWidget(label2)
        container_layout.addWidget(QLabel())

        # Сетка для расположения элементов
        grid_layout = QGridLayout()

        # Создаем элементы для сетки
        uname = os.uname()
        grid_label1 = QLabel(self.tr("Kernel:"))
        grid_label2 = QLabel(uname.release)
        self.text.append('{} {}'.format(grid_label1.text(), grid_label2.text()))

        grid_label3 = QLabel(self.tr("Display server:"))
        grid_label4 = QLabel(my_utils.get_display_server())
        self.text.append('{} {}'.format(grid_label3.text(), grid_label4.text()))

        # cpu_name, num_cores = my_utils.get_cpu_info_from_proc()
        # self.formLayout.addRow(self.tr("Processor:"), QLabel("{} x {}".format(num_cores, cpu_name)))

        total_memory, used_memory, free_memory = my_utils.get_memory_info_from_free()
        grid_label5 = QLabel(self.tr("Memory (used/total):"))
        gb = self.tr("GB")
        s = f"{used_memory / (1024 ** 3):.2f} {gb}  /  {total_memory / (1024 ** 3):.2f} {gb}"
        grid_label6 = QLabel(s)
        self.text.append('{} {}\n'.format(grid_label5.text(), grid_label6.text()))

        # Устанавливаем выравнивание для левого столбца (по правому краю)
        grid_label1.setAlignment(Qt.AlignRight | Qt.AlignVCenter)
        grid_label3.setAlignment(Qt.AlignRight | Qt.AlignVCenter)
        grid_label5.setAlignment(Qt.AlignRight | Qt.AlignVCenter)

        # Добавляем элементы в сетку
        grid_layout.addWidget(grid_label1, 0, 0)
        grid_layout.addWidget(grid_label2, 0, 1)
        grid_layout.addWidget(grid_label3, 1, 0)
        grid_layout.addWidget(grid_label4, 1, 1)
        grid_layout.addWidget(grid_label5, 2, 0)
        grid_layout.addWidget(grid_label6, 2, 1)

        # Добавляем сетку в контейнер
        container_layout.addLayout(grid_layout)

        # Добавляем Spacer снизу
        bottom_spacer = QSpacerItem(20, 40, QSizePolicy.Minimum, QSizePolicy.Expanding)
        container_layout.addItem(bottom_spacer)

        # Добавляем контейнер в scroll_area
        scroll_area.setWidget(container)

        # Центрируем QScrollArea внутри основного лэйаута
        main_layout.addWidget(scroll_area)

        # Устанавливаем основной лэйаут для окна
        self.setLayout(main_layout)

        # Устанавливаем поведение контекстного меню
        self.setContextMenuPolicy(Qt.CustomContextMenu)
        self.customContextMenuRequested.connect(self.show_context_menu)


    def show_context_menu(self, pos):
        context_menu = QMenu(self)

        # Добавляем пункт "Скопировать текст"
        copy_action = QAction(self.tr("Copy text"), self)
        context_menu.addAction(copy_action)

        # Связываем действие с функцией
        copy_action.triggered.connect(self.copy_text)

        # Показываем контекстное меню
        context_menu.exec_(self.mapToGlobal(pos))


    def copy_text(self):
        # Собираем весь текст с QLabel
        text_to_copy = "\n".join(self.text)

        # Копируем в буфер обмена
        clipboard = QApplication.clipboard()
        clipboard.setText(text_to_copy)
        # print("Текст скопирован в буфер обмена.")


class PluginAbout(plugins.Base):
    def __init__(self):
        super().__init__("about", 1)
        self.node = None
        self.about_widget = None

    def start(self, plist, pane):
        self.node = QStandardItem(self.tr("About system"))
        self.node.setData(self.getName())
        plist.appendRow([self.node])

        main_palette = pane.window().palette()

        self.about_widget = AboutWidget(main_palette)
        pane.addWidget(self.about_widget)
