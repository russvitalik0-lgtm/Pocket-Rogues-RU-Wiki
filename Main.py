# Импорты
import sys
import os
import ctypes
from PyQt5.QtCore import Qt
from PyQt5.QtGui import QIcon
from PyQt5.QtWidgets import *
import json
from random import randint

app = QApplication([])

from pages.Wiki import WikiPage
from pages.Latest import LatestPage
from pages.Tips import TipsPage
from pages.history_manager import HistoryManager

# Создание и редакция окна и приложения
class MainWindow(QWidget):
    def __init__(self):
        super().__init__()

        # Меняем окно
        self.setWindowTitle('Pocket Rogues: RU-Wiki')
        self.setMinimumSize(1800, 900)

        # Главный вертикальный layout
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.setSpacing(0)

        # Контейнер для контента: Горизонтальный layout
        content_widget = QWidget()
        content_layout = QHBoxLayout(content_widget)
        content_layout.setContentsMargins(10, 10, 10, 10)

        # Добавляем страницы
        self.add_page()

        # Закрепляем страницы
        self.latest_page.page_opened.connect(self.open_wiki_page)

        # Добавление панелей
        left_panel = QVBoxLayout()
        left_panel.addWidget(QLabel("- Вкладки -"), alignment=Qt.AlignCenter)
        left_panel.addWidget(self.list_widget)
        left_panel.addStretch()

        content_layout.addLayout(left_panel)
        content_layout.addWidget(self.stacked, 1)

        main_layout.addWidget(content_widget)

        # По умолчанию выбираем Вики
        self.list_widget.setCurrentRow(0)

    def add_page(self):
        """Добавляет вкладки страниц"""
        # Основной список
        self.list_widget = QListWidget()
        for item in ['Википедия', 'Недавние', 'Заметки']:
            self.list_widget.addItem(item)
        self.list_widget.setFixedWidth(150)
        self.list_widget.setSpacing(5)
        self.list_widget.currentRowChanged.connect(self.switch_page)
    
        # Стек страниц
        self.stacked = QStackedWidget()
        self.wiki_page = WikiPage()
        self.latest_page = LatestPage()
        self.tips_page = TipsPage()
        
        self.stacked.addWidget(self.wiki_page)
        self.stacked.addWidget(self.latest_page)
        self.stacked.addWidget(self.tips_page)

    def switch_page(self, index):
        self.stacked.setCurrentIndex(index)

    def open_wiki_page(self, page_id):
        """Переключает на страницу в Википедии"""
        # Переключаем вкладку на "Википедия" (индекс 0)
        self.list_widget.setCurrentRow(0)

        # Переключаем страницу внутри WikiPage
        self.wiki_page.change_section(page_id)


window = MainWindow()
window.show()
sys.exit(app.exec_())