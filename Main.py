# Импорты
import sys
import os
import ctypes
from PyQt5.QtCore import Qt
from PyQt5.QtGui import QIcon
from PyQt5.QtWidgets import *
import json
from random import randint

from pages.Wiki import WikiPage
from pages.Latest import LatestPage
from pages.Tips import TipsPage
from pages.Promo import PromoPage
from pages.Contacts import ContactPage
from pages.history_manager import HistoryManager

# Создание и редакция окна и приложения
app = QApplication([])
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

        left_panel.addWidget(self.addons_label, alignment=Qt.AlignCenter)
        left_panel.addWidget(self.addons_list_widget)
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
        for item in ['Википедия', 'Недавние', 'Заметки', 'Дополнения', 'Обратная связь']:
            self.list_widget.addItem(item)
        self.list_widget.setFixedWidth(150)
        self.list_widget.setSpacing(5)
        self.list_widget.currentRowChanged.connect(self.switch_page)

        # Список для дополнений
        self.addons_list_widget = QListWidget()
        self.addons_list_widget.setFixedWidth(150)
        self.addons_list_widget.setSpacing(5)
        self.addons_list_widget.currentRowChanged.connect(self.switch_addon_page)
        self.addons_list_widget.hide()

        self.addons_label = QLabel("- Дополнения -")
        self.addons_label.hide()
    
        # Стек страниц
        self.stacked = QStackedWidget()
        self.wiki_page = WikiPage()
        self.latest_page = LatestPage()
        self.tips_page = TipsPage()
        self.promo_page = PromoPage()
        self.promo_page.addon_activated.connect(self.on_addon_changed)
        self.contact = ContactPage()
        
        self.stacked.addWidget(self.wiki_page)
        self.stacked.addWidget(self.latest_page)
        self.stacked.addWidget(self.tips_page)
        self.stacked.addWidget(self.promo_page)
        self.stacked.addWidget(self.contact)

        for code in self.promo_page.addons_manager.get_active_addons():
            self.on_addon_changed(code, True)

    def switch_page(self, index):
        self.stacked.setCurrentIndex(index)

    def open_wiki_page(self, page_id):
        """Переключает на страницу в Википедии"""
        # Переключаем вкладку на "Википедия" (индекс 0)
        self.list_widget.setCurrentRow(0)

        # Переключаем страницу внутри WikiPage
        self.wiki_page.change_section(page_id)

    def add_tab(self, title, page_widget, is_addon=False):
        if is_addon:
            # Добавляем в список дополнений
            self.addons_list_widget.addItem(title)
            self.addons_list_widget.show()
            self.addons_label.show()
            # Добавляем в стек
            self.stacked.addWidget(page_widget)
        else:
            # Обычная вкладка
            self.list_widget.addItem(title)
            self.stacked.addWidget(page_widget)

    def remove_tab(self, title):
        # Ищем в списке дополнений
        for i in range(self.addons_list_widget.count()):
            if self.addons_list_widget.item(i).text() == title:
                self.addons_list_widget.takeItem(i)
                widget = self.stacked.widget(i + 5)
                self.stacked.removeWidget(widget)
                widget.deleteLater()
                break

        if self.addons_list_widget.count() == 0:
            self.addons_list_widget.hide()
            self.addons_label.hide()

    def switch_addon_page(self, index):
        """Переключает страницу для вкладок дополнений"""
        self.stacked.setCurrentIndex(index + 5)

    def on_addon_changed(self, code, is_active):
        """Обрабатывает изменение состояния дополнений"""
        addon_info = self.promo_page.addons_manager.addons.get(code)

        if addon_info and "tab_title" in addon_info:
            tab_title = addon_info["tab_title"]
            if is_active:
                page_widget = QWidget()
                self.add_tab(tab_title, page_widget, is_addon=True)
            else:
                self.remove_tab(tab_title)

        #if code == "AddPrototype":
        #    if is_active:
        #        self.tips_page.add_addon_tab(prototype_widget, "Прототип")
        #    else:
        #        self.tips_page.remove_addon_tab("Прототип")

# Создание виджетов


window = MainWindow()
window.show()
sys.exit(app.exec_())