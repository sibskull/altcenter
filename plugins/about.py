#!/usr/bin/python3

from PyQt5.QtWidgets import (QWidget, QVBoxLayout, QLabel,
                            QGridLayout, QScrollArea, QSpacerItem, QSizePolicy)
from PyQt5.QtGui import QStandardItem, QFont
from PyQt5.QtCore import Qt, QSize

import os
import sys
# import locale

import plugins
import my_utils

class AboutWidget(QWidget):
    def __init__(self):
        super().__init__()
        self.initUI()

    def initUI(self):
        # Основной лэйаут для окна
        main_layout = QVBoxLayout()

        # Создание QScrollArea
        scroll_area = QScrollArea(self)
        scroll_area.setWidgetResizable(True)  # Ресайз области прокрутки

        # Создание контейнера для виджетов внутри QScrollArea
        container = QWidget()
        font = QFont('Sans', 11)
        container.setFont(font)
        container_layout = QVBoxLayout(container)  # Внутренний лэйаут для контейнера
        container_layout.setSpacing(10)

        # Добавляем Spacer сверху (с помощью QSizePolicy.Expanding)
        top_spacer = QSpacerItem(20, 40, QSizePolicy.Minimum, QSizePolicy.Expanding)
        container_layout.addItem(top_spacer)

        # Создаем метки
        os_info = my_utils.parse_os_release()
        s = "{} {} {}".format(os_info["PRETTY_NAME"], os_info["NAME"], os_info["VERSION"])
        label1 = QLabel(s)
        label1.setAlignment(Qt.AlignCenter)
        label1.setWordWrap(True)
        label_font = container.font()
        label_font.setPointSize(label_font.pointSize() + 18)
        # label_font.setBold(True)
        label1.setFont(label_font)

        label2 = QLabel('<a href="https://www.basealt.ru/">https://www.basealt.ru/</a>')
        label2.setAlignment(Qt.AlignCenter)

        # Добавляем метки в контейнер
        container_layout.addWidget(label1)
        container_layout.addWidget(label2)

        # Сетка для расположения элементов
        grid_layout = QGridLayout()

        # Создаем элементы для сетки
        uname = os.uname()
        grid_label1 = QLabel(self.tr("Kernel:"))
        grid_label2 = QLabel(uname.release)

        grid_label3 = QLabel(self.tr("Display server:"))
        grid_label4 = QLabel(my_utils.get_display_server())

        # cpu_name, num_cores = my_utils.get_cpu_info_from_proc()
        # self.formLayout.addRow(self.tr("Processor:"), QLabel("{} x {}".format(num_cores, cpu_name)))

        total_memory, used_memory, free_memory = my_utils.get_memory_info_from_free()
        grid_label5 = QLabel(self.tr("Memory (used/total):"))
        gb = self.tr("GB")
        s = f"{used_memory / (1024 ** 3):.2f} {gb}  /  {total_memory / (1024 ** 3):.2f} {gb}"
        grid_label6 = QLabel(s)

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


class PluginAbout(plugins.Base):
    def __init__(self):
        super().__init__(1)
        self.node = None
        self.about_widget = None

    def start(self, plist, pane):
        self.node = QStandardItem(self.tr("About system"))
        plist.appendRow([self.node])

        self.about_widget = AboutWidget()
        pane.addWidget(self.about_widget)


if __name__ == '__main__':
    from PyQt5.QtWidgets import QApplication

    app = QApplication(sys.argv)
    window = AboutWidget()
    window.show()
    sys.exit(app.exec_())
