# TipsPage
from PyQt6.QtCore import Qt, pyqtSignal, QTimer
from PyQt6.QtWidgets import *
from .Base import BasePage
from .Base import ImageLoader
import markdown
import os

from .syntax_highlighters import MarkdownHighlighter

class TipsPage(BasePage):
    def __init__(self, parent=None):
        super().__init__(parent)

        self.add_title("Заметки")
        self.description = QLabel("Это описание")
        self.description.setObjectName("pageDescription")

        # Создаем метку
        self.image_label = QLabel("Загрузка...")
        self.image_label.setObjectName("pageLogo")
        self.image_label.setAlignment(Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignTop)

        # Размещаем
        Hlayout = QHBoxLayout()
        Hlayout.addWidget(self.description, alignment = Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignVCenter)
        Hlayout.addWidget(self.image_label, alignment = Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignTop)
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

        # debounce
        self.preview_timer = QTimer()
        self.preview_timer.setSingleShot(True)
        self.preview_timer.timeout.connect(self._do_update_preview)

        # Поле для Markdown
        self.md_edit = QPlainTextEdit()
        self.md_edit.setObjectName("notesEditor")
        self.md_edit.setPlaceholderText("Поле для записи Ваших заметок. Имеет поддержку Markdown.")
        self.md_edit.textChanged.connect(self._on_md_text_changed)
        self.md_edit.verticalScrollBar().valueChanged.connect(self._sync_scroll)
        self.md_highlighter = MarkdownHighlighter(self.md_edit.document())

        # Поле для просмотра
        self.preview_edit = QTextBrowser()
        self.preview_edit.setObjectName("notesPreview")
        self.preview_edit.setPlaceholderText("Поле для просмотра Ваших заметок в более красивом стиле. Отображает Markdown.")

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

    def _do_update_preview(self):
        """Фактическое обновление preview (вызывается по таймеру)"""
        # Конвертация MD в HTML
        html = markdown.markdown(self.md_edit.toPlainText())
        self.preview_edit.setHtml(html)

        QTimer.singleShot(0, self._sync_scroll)

        self.save_notes()

    def _on_md_text_changed(self):
        """Перезапускает таймер обновления preview при каждом изменении"""
        self.preview_timer.start(500)

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

    def _sync_scroll(self):
        """Синхронизирует скролл preview с md_edit по относительный позиции"""
        src_bar = self.md_edit.verticalScrollBar()
        dst_bar = self.preview_edit.verticalScrollBar()

        src_max = src_bar.maximum()
        dst_max = dst_bar.maximum()

        if src_max == 0 or dst_max == 0:
            return

        # Относительная позиция (0.0 - 1.0)
        ratio = src_bar.value() / src_max

        # Устанавливаем в правом
        dst_bar.setValue(int(ratio * dst_max))