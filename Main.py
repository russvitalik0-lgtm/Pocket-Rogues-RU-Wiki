# Импорты
import sys
import os
import ctypes
from PyQt5.QtCore import Qt
from PyQt5.QtGui import QIcon
from PyQt5.QtWidgets import *
import json
from random import randint

# Ставим флаг до QApplication для корректной работы приложения
QApplication.setAttribute(Qt.AA_ShareOpenGLContexts)
app = QApplication([])
qss_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "themes", "light.qss")
try:
    with open(qss_path, "r", encoding="utf-8") as f:
        app.setStyleSheet(f.read())
except FileNotFoundError:
    print(f"QSS-файл не найден: {qss_path}")

from pages.Wiki import WikiPage
from pages.Latest import LatestPage
from pages.Tips import TipsPage
from pages.Saved import SavedPage
from pages.history_manager import HistoryManager
from pages.Base import saved_manager

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
        self.saved_page.page_opened.connect(self.open_wiki_page)

        # Добавление панелей
        self.left_panel = QWidget()
        self.left_panel.setObjectName("leftPanel")
        left_panel_title = QLabel("- Вкладки -")
        left_panel_title.setObjectName("leftPanelTitle")
        left_panel_inner = QVBoxLayout(self.left_panel)
        left_panel_inner.setContentsMargins(0, 0, 0, 0)
        left_panel_inner.addWidget(left_panel_title, alignment=Qt.AlignCenter)
        left_panel_inner.addWidget(self.list_widget)
        left_panel_inner.addStretch()

        content_layout.addWidget(self.left_panel)
        content_layout.addWidget(self.stacked, 1)

        main_layout.addWidget(content_widget)

        # По умолчанию выбираем Вики
        self.list_widget.setCurrentRow(0)

        # Сигналы
        self.wiki_page.fullscreen_requested.connect(self.toggle_fullscreen)
        self.wiki_page.save_toggle_requested.connect(self.toggle_save)

    def add_page(self):
        """Добавляет вкладки страниц"""
        # Основной список
        self.list_widget = QListWidget()
        self.list_widget.setObjectName("mainTabsList")
        for item in ['Википедия', 'Недавние', 'Сохранённое', 'Заметки']:
            self.list_widget.addItem(item)
        self.list_widget.setFixedWidth(150)
        self.list_widget.setSpacing(5)
        self.list_widget.currentRowChanged.connect(self.switch_page)
    
        # Стек страниц
        self.stacked = QStackedWidget()
        self.wiki_page = WikiPage()
        self.latest_page = LatestPage()
        self.tips_page = TipsPage()
        self.saved_page = SavedPage()
        
        self.stacked.addWidget(self.wiki_page)
        self.stacked.addWidget(self.latest_page)
        self.stacked.addWidget(self.saved_page)
        self.stacked.addWidget(self.tips_page)

    def switch_page(self, index):
        self.stacked.setCurrentIndex(index)

    def open_wiki_page(self, page_id):
        """Переключает на страницу в Википедии"""
        # Переключаем вкладку на "Википедия" (индекс 0)
        self.list_widget.setCurrentRow(0)

        # Переключаем страницу внутри WikiPage
        self.wiki_page.change_section(page_id)

    def toggle_fullscreen(self):
        """Переключает полноэкранный режим главного окна"""
        if self.left_panel.isVisible():
            self.left_panel.hide()
            self.wiki_page.set_reading_mode(True)
        else:
            self.left_panel.show()
            self.wiki_page.set_reading_mode(False)

    def toggle_save(self):
        """Переключает сохранение текущей страницы"""
        page_id = self.wiki_page.current_page_id
        if not page_id:
            return
        saved_manager.toggle(page_id)
        self.wiki_page._update_save_icon()


window = MainWindow()
window.show()
sys.exit(app.exec_())