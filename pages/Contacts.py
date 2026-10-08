from PyQt5.QtCore import Qt, pyqtSignal, QTimer
from PyQt5.QtWidgets import *
from .Base import BasePage
from .Base import ImageLoader

class ContactPage(BasePage):
    def __init__(self, parent=None):
        super().__init__(parent)

        self.add_title("Обратная Связь")


        # Создаем метку
        self.image_label = QLabel("Загрузка...")
        self.image_label.setAlignment(Qt.AlignRight | Qt.AlignTop)

        self.description_label = QLabel("Это описание") # Создаем описание раздела
        self.description_label.setAlignment(Qt.AlignLeft | Qt.AlignVCenter)
    
        # Крепим виджеты
        Hlayout = QHBoxLayout()
        Hlayout.addWidget(self.description_label)
        Hlayout.addWidget(self.image_label, alignment= Qt.AlignRight | Qt.AlignTop)
        Hlayout.setContentsMargins(0,0,0,0)

        # Крепим к основному лайауту
        self.layout.addLayout(Hlayout)
        

        # Запуск загрузки картинки в отдельном потоке
        self.loader = ImageLoader()
        self.loader.finished.connect(self.on_image_loaded)
        self.loader.error.connect(self.on_image_error)
        self.loader.start()

        # Добавляем разделитель и пространство под ним
        self.add_separator()
        self.add_stretch()

    def on_image_loaded(self, pixmap):
        """Вызывается, когда картинка успешно загружена"""
        self.image_label.setPixmap(pixmap)
        self.image_label.setText("") # Убираем текст "Загрузка"

    def on_image_error(self):
        """Вызывается при ошибке"""
        self.image_label.setText("Ошибка загрузки")
        self.image_label.setStyleSheet("color: red;")