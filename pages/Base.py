# Prototype for pages
from PyQt6.QtCore import Qt, QThread, pyqtSignal, QSize
from PyQt6.QtGui import QPixmap, QImage
from PyQt6.QtWidgets import *
import sys
import os
import requests
import re # Модуль для работы с регулярными выражениями. Удалит HTML-Теги из текста
from .history_manager import HistoryManager
from .saved_manager import SavedManager


history_manager = HistoryManager()
saved_manager = SavedManager()
some_url = "https://static.wikia.nocookie.net/pocketrogues/images/e/e6/Site-logo.png/revision/latest?cb=20210610092016&path-prefix=ru"

# Создаем поток для загрузки картинки, чтобы не морозить интерфейс
class ImageLoader(QThread):
    finished = pyqtSignal(QPixmap)
    error = pyqtSignal(str)

    def run(self):
        try:
            headers = {
                "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
                            "(KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
                "Accept": "image/avif,image/webp,image/apng,image/*,*/*;q=0.8",
                "Accept-Language": "ru-RU,ru;q=0.9,en-US;q=0.8,en;q=0.7",
                "Referer": "https://pocketrogues.fandom.com/",
            }
            response = requests.get(some_url, headers=headers, timeout=10)
            response.raise_for_status()

            image = QImage()
            image.loadFromData(response.content)

            if image.isNull():
                self.error.emit("Отсутствует подключение к сети")
                return

            pixmap = QPixmap.fromImage(image)
            fixed_size = QSize(150, 75)
            scaled_pixmap = pixmap.scaled(
                fixed_size,
                Qt.AspectRatioMode.KeepAspectRatio,
                Qt.TransformationMode.SmoothTransformation
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
        title.setObjectName("pageTitle")
        self.layout.addWidget(title)
    
    def add_separator(self):
        """Добавляет разделительную линию"""
        line = QFrame()
        line.setObjectName("pageSeparator")
        line.setFrameShape(QFrame.Shape.HLine)
        self.layout.addWidget(line)
    
    def add_stretch(self):
        """Добавляет растягивающееся пространство внизу"""
        self.layout.addStretch()

    def _make_empty_widget(self, text, logo_pixmap=None, logo_size=None):
        """Создаёт заглушку: картинка (если есть) + текст"""
        container = QWidget()
        container.setObjectName("emptyContainer")
        layout = QVBoxLayout(container)
        layout.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.setSpacing(15)

        if logo_pixmap and not logo_pixmap.isNull():
            logo = QLabel()
            logo.setObjectName("emptyLogo")
            logo.setAlignment(Qt.AlignmentFlag.AlignCenter)
            if logo_size is not None:
                # Приводим к QSize (если передали кортеж)
                if isinstance(logo_size, tuple):
                    logo_size = QSize(*logo_size)
                logo_pixmap = logo_pixmap.scaled(
                    logo_size,
                    Qt.AspectRatioMode.KeepAspectRatio,
                    Qt.TransformationMode.SmoothTransformation
                )

            logo.setPixmap(logo_pixmap)
            layout.addWidget(logo)

        label = QLabel(text)
        label.setObjectName("emptyLabel")
        label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(label)

        return container

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

    """А теперь чистка"""

    # 1. Удаляем style и script блоки
    html_content = re.sub(r'<style[^>]*>.*?</style>', '', html_content, flags=re.DOTALL)
    html_content = re.sub(r'<script[^>]*>.*?</script>', '', html_content, flags=re.DOTALL)

    # 2. Отрезаем всё до <h1>
    idx = html_content.find("<h1")
    if idx != -1:
        html_content = html_content[idx:]

    # 3. Убираем aside/nav/table/details, если они ниже <h1>
    html_content = re.sub(r'<aside[^>]*>.*?</aside>', '', html_content, flags=re.DOTALL)
    html_content = re.sub(r'<nav[^>]*>.*?</nav>', '', html_content, flags=re.DOTALL)
    html_content = re.sub(r'<table[^>]*>.*?</table>', '', html_content, flags=re.DOTALL)
    html_content = re.sub(r'<details[^>]*>.*?</details>', '', html_content, flags=re.DOTALL)

    # 4. Каждый тег -> перевод строки
    # Сначала инлайновые - удаляем без следа
    inline_tags = r'</?(b|i|u|a|strong|em|span|small|sup|sub|code|abbr)[^>]*>'
    text = re.sub(inline_tags, '', html_content)

    # Потом блочные - заменяем на \n
    block_tags = r'</?(h[1-6]|p|li|ul|ol|div|br|tr|td|th|blockquote|figure|figcaption|aside|nav|header|footer|section|article)[^>]*>'
    text = re.sub(block_tags, '\n', text)

    # И на всякий случай - все оставшиеся теги удаляем без замены
    text = re.sub(r'<[^>]+>', '', text)

    # 5. Схлопываем подряд идущие пробелы и переводы строк, но не одиночные \n
    text = re.sub(r'[ \t]+', ' ', text)       # много пробелов - один
    text = re.sub(r' *\n *', '\n', text)      # пробелы вокруг \n убираем
    text = re.sub(r'\n{2,}', '\n', text)      # двойные \n - один
    text = text.strip()

    # 6. Обрезка
    lines = [line for line in text.split('\n') if line.strip()]
    if len(lines) >= 2:
        text = lines[0] + '\n' + lines[1]
    else:
        text = lines[0] if lines else ''

    # 6.1 Умная обрезка по точке
    MAX_LEN = 300
    MIN_POINT = int(MAX_LEN * 0.5)

    if len(text) > MAX_LEN:
        # Ищем последнюю точку перед лимитом
        chunk = text[:MAX_LEN]
        last_dot = chunk.rfind('.')

        if last_dot >= MIN_POINT:
            # Точка близко к лимиту - обрезаем по ней
            text = chunk[:last_dot + 1]
        else:
            # Если точки нет - обрезаем по пробелу
            last_space = chunk.rfind(' ')
            if last_space > MIN_POINT:
                text = chunk[:last_space]
            else:
                text = chunk
            text += '...'

    return text