# TipsPage
from PyQt5.QtCore import Qt, pyqtSignal
from PyQt5.QtWidgets import *
from .Base import BasePage
from .Base import ImageLoader
import markdown
import os

class TipsPage(BasePage):
    def __init__(self, parent=None):
        super().__init__(parent)

        self.add_title("Заметки")
        self.description = QLabel("Это описание")

        # Создаем метку
        self.image_label = QLabel("Загрузка...")
        self.image_label.setAlignment(Qt.AlignRight | Qt.AlignTop)

        # Размещаем
        Hlayout = QHBoxLayout()
        Hlayout.addWidget(self.description, alignment = Qt.AlignLeft | Qt.AlignVCenter)
        Hlayout.addWidget(self.image_label, alignment = Qt.AlignRight | Qt.AlignTop)
        Hlayout.setContentsMargins(0,0,0,0)

        # Крепим к основному лайауту
        self.layout.addLayout(Hlayout)
    
        # Запуск загрузки картинки в отедльном потоке
        self.loader = ImageLoader()
        self.loader.finished.connect(self.on_image_loaded)
        self.loader.error.connect(self.on_image_error)
        self.loader.start()
    
        # Разделитель
        self.add_separator()

        """Начинаем делать заметки"""
        # Лайауты
        self.editors_layout = QHBoxLayout()
        self.layout.addLayout(self.editors_layout, 1)

        # Поле для Markdown
        self.md_edit = QTextEdit()
        self.md_edit.setPlaceholderText("Поле для записи Ваших заметок. Имеет поддержку Markdown и HTML.")
        self.md_edit.textChanged.connect(self.update_preview)

        # Поле для просмотра
        self.preview_edit = QTextBrowser()
        self.preview_edit.setPlaceholderText("Поле для просмотра Ваших заметок в более красивом стиле. Отображает Markdown и HTML.")

        # Размещаем
        self.editors_layout.addWidget(self.md_edit, 1)
        self.editors_layout.addWidget(self.preview_edit, 1)

        # Загружаем Заметки
        self.load_notes()

    def on_image_loaded(self, pixmap):
        """Вызывается, когда картинка успешно загружена"""
        self.image_label.setPixmap(pixmap)
        self.image_label.setText("") # Убираем текст "Загрузка"
    
    def on_image_error(self):
        """Вызывается при ошибке"""
        self.image_label.setText("Ошибка загрузки")
        self.image_label.setStyleSheet("color: red;")

    def update_preview(self):
        """Обновляет окно просмотра при изменении текста"""
        # Конвертация MD в HTML
        html = markdown.markdown(self.md_edit.toPlainText())
        self.preview_edit.setHtml(html)
        self.save_notes()

    def save_notes(self):
        # Получаем путь к папке со скриптом
        current_dir = os.path.dirname(os.path.abspath(__file__))
        file_path = os.path.join(current_dir, "notes.md")

        with open(file_path, "w", encoding="utf-8") as f:
            f.write(self.md_edit.toPlainText())

    def load_notes(self):
        current_dir = os.path.dirname(os.path.abspath(__file__))
        file_path = os.path.join(current_dir, "notes.md")
        
        try:
            with open(file_path, "r", encoding="utf-8") as f:
                self.md_edit.setPlainText(f.read())
        except FileNotFoundError:
            pass