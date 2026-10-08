# Prototype for pages
from PyQt5.QtCore import Qt, QThread, pyqtSignal, QSize
from PyQt5.QtGui import QPixmap, QImage
from PyQt5.QtWidgets import *
import sys
import os
import requests
import re # Модуль для работы с регулярными выражениями. Удалит HTML-Теги из текста
from .history_manager import HistoryManager


history_manager = HistoryManager()
some_url = "https://static.wikia.nocookie.net/pocketrogues/images/e/e6/Site-logo.png/revision/latest?cb=20210610092016&path-prefix=ru"

# Создаем поток для загрузки картинки, чтобы не морозить интерфейс
class ImageLoader(QThread):
    finished = pyqtSignal(QPixmap)
    error = pyqtSignal(str)

    def run(self):
        try:
            response = requests.get(some_url)
            response.raise_for_status()  # Проверка на ошибки HTTP

            image = QImage()
            image.loadFromData(response.content)

            if image.isNull(): # Проверка переменной на наличие хоть чего-либо
                self.error.emit("Отсутствует подключение к сети")
                return

            pixmap = QPixmap.fromImage(image)
            fixed_size = QSize(150,75)
            scaled_pixmap = pixmap.scaled(
                fixed_size,
                Qt.KeepAspectRatio,
                Qt.SmoothTransformation
            )

            self.finished.emit(scaled_pixmap)
        except Exception as e:
            self.error.emit(f"Ошибка загрузки: {str(e)}")

class BasePage(QWidget):
    """Базовый класс для всех страниц"""
    def __init__(self, parent=None):
        super().__init__(parent)
        self.layout = QVBoxLayout(self)
        self.layout.setSpacing(10)
        self.layout.setContentsMargins(10, 10, 10, 10)
    
    def add_title(self, text):
        """Добавляет заголовок страницы"""
        title = QLabel(text)
        title.setStyleSheet("font-size: 18px; font-weight: bold;")
        self.layout.addWidget(title)
    
    def add_separator(self):
        """Добавляет разделительную линию"""
        line = QFrame()
        line.setFrameShape(QFrame.HLine)
        line.setStyleSheet("background-color: #3c3c3c; height: 1px;")
        self.layout.addWidget(line)
    
    def add_stretch(self):
        """Добавляет растягивающееся пространство внизу"""
        self.layout.addStretch()

def load_html(file_name):
    """Загружает HTML из папки WikiContent"""
    # Получаем абсолютный путь к папке со скриптом
    current_dir = os.path.dirname(os.path.abspath(__file__))
    file_path = os.path.join(current_dir, "WikiContent", file_name)
    
    try:
        with open(file_path, "r", encoding="utf-8") as f:
            return f.read()
    except FileNotFoundError: # !!! ОБЯЗАТЕЛЬНО ЗАМЕНИТЬ ПОСЛЕ ОКОНЧАНИЯ ИСПОЛЬЗОВАНИЯ !!!
        # Создаем шаблон
        template = f"""<!DOCTYPE html>
<html>
<head>
    <title>{file_name}</title>
</head>
<body>
    <h1>{file_name.replace('.html', '')}</h1>
    <p>Страница в разработке...</p>
</body>
</html>"""

        # Сохраняем файл
        with open(file_path, "w", encoding="utf-8") as f:
            f.write(template)

        # Возвращаем созданный шаблон
        return template

def get_page_preview(page_id):
    """Получает превью текста страницы"""
    # Преобразуем ID в имя файла
    file_name = page_id.lower() + ".html" # Айди "Warrior" преобразуется к нижнему регистру: warrior.html

    # Загружаем HTML
    html_content = load_html(file_name)

    # Удаляем style и script блоки
    html_content = re.sub(r'<style[^>]*>.*?</style>', '', html_content, flags=re.DOTALL)
    html_content = re.sub(r'<script[^>]*>.*?</script>', '', html_content, flags=re.DOTALL)

    # Убираем HTML-теги
    text = re.sub(r'<[^>]+>', '', html_content) 

    # Убираем лишние пробелы и переносы
    text = re.sub(r'\s+', ' ', text)
    text = text.strip()

    # Обрезаем до 100 символов
    if len(text) > 210:
        text = text[:207] + "..."

    return text