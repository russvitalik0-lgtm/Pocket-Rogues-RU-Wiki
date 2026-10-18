# LinkDialog - гиперссылки
from PyQt6.QtWidgets import *
from PyQt6.QtCore import Qt
from pathlib import Path

from pages.Base import READY_PAGES

class LinkDialog(QDialog):
    """Диалог вставки гиперссылки в VE"""

    def __init__(self, parent=None, selected_text="", anchors=None):
        super().__init__(parent)
        self.anchors = anchors or []

        self.setWindowTitle("Вставить ссылку")
        self.setMinimumWidth(400)
        self.setBaseSize(400, 200)
        self.setMaximumHeight(350)

        layout = QVBoxLayout(self)

        # Поле текста
        text_label = QLabel("Текст ссылки:")
        self.text_input = QLineEdit()
        self.text_input.setPlaceholderText("Визуальный текст, видимый на странице")
        layout.addWidget(text_label)
        layout.addWidget(self.text_input)

        layout.addSpacing(10)

        # поле URL
        url_label = QLabel("URL или название страницы:")
        self.url_input = QLineEdit()
        self.url_input.setPlaceholderText("Введите вашу ссылку...")
        self.url_input.textChanged.connect(self._on_url_changed)
        layout.addWidget(url_label)
        layout.addWidget(self.url_input)

        # Подсказка
        hint = QLabel(
            "Примеры:<br>"
            "• <code>https://example.com</code> - внешняя ссылка<br>"
            "• <code>#Быстрые_атаки</code> - Якорная ссылка в текущей странице<br>"
            "• <code>@Necromancer</code> - Ссылка на другую страницу приложения (Некромант)<br>"
            "• <code>None</code> - удалить ссылку с выделенного фрагмента"
        )
        hint.setStyleSheet("color: #888; font-size: 11px;")
        hint.setWordWrap(True)
        layout.addWidget(hint)

        # Автоподбор
        self.suggestions_list = QListWidget()
        self.suggestions_list.setMaximumHeight(120)
        self.suggestions_list.setVisible(False)
        self.suggestions_list.itemClicked.connect(self._on_suggestion_clicked)
        layout.addWidget(self.suggestions_list)

        # Если передан выделенный текст - предзаполняем и блокируем
        if selected_text:
            self.text_input.setText(selected_text)
            self.text_input.setReadOnly(True)
            self.text_input.setStyleSheet("background-color: #2a2a2a; color: #aaa;")

        # Кнопки
        buttons = QHBoxLayout()
        buttons.addStretch()

        self.ok_btn = QPushButton("Вставить")
        self.ok_btn.setDefault(True)
        self.ok_btn.clicked.connect(self._on_ok)

        self.cancel_btn = QPushButton("Отмена")
        self.cancel_btn.clicked.connect(self.reject)

        buttons.addWidget(self.ok_btn)
        buttons.addWidget(self.cancel_btn)
        layout.addLayout(buttons)

    def _on_ok(self):
        """Валидация перед принятием"""
        self.suggestions_list.setVisible(False)

        url = self.get_url()
        if url is None:
            return
        if not url:
            QMessageBox.warning(self, "Ошибка", "Введите URL или название страницы")
            return

        if url == "None":
            self.accept()
            return

        text = self.text_input.text().strip()
        if not text:
            QMessageBox.warning(self, "Ошибка", "Введите видимый текст ссылки")
            return

        self.accept()

    def get_url(self):
        """Возвращает нормализованный URL"""
        url = self.url_input.text().strip()

        if not url:
            return ""

        # Удаление ссылки
        if url == "None":
            return "None"

        # Внешняя ссылка
        if url.startswith(("http://", "https://")):
            return url

        # Якорь в текущей странице
        if url.startswith("#"):
            return url

        # Страница приложения
        if url.startswith("@"):
            return url

        # Без префикса - ошибка
        QMessageBox.warning(
            self, "Ошибка",
            "Укажите префикс:\n"
            "• '#' для якоря в текущей странице\n"
            "• '@' для страницы приложения\n"
            "• 'https://' для внешней ссылки"
        )
        return None

    def get_text(self):
        """Возвращает текст ссылки"""
        return self.text_input.text().strip()

    def _on_url_changed(self, text):
        """Обновляет подсказки по готовым страницам при вводе URL"""
        text = text.strip().lower()

        # Если пусто, коротко или начинается с http - не подсказываем
        if len(text) <= 2:
            self.suggestions_list.setVisible(False)
            return
        if text.startswith(("http://", "https://")):
            self.suggestions_list.setVisible(False)
            return

        # Якоря
        if text.startswith("#"):
            # Поиск по заголовкам текущей страницы
            search = text[1:].lower()
            if len(search) < 1:
                self.suggestions_list.setVisible(False)
                return

            matches = []
            for anchor in self.anchors:
                anchor_id = anchor.get("id", "")
                anchor_text = anchor.get("text", "")
                if search in anchor_id.lower() or search in anchor_text.lower():
                    matches.append(anchor)

            if not matches:
                self.suggestions_list.setVisible(False)
                return

            matches = matches[:5]
            
            self.suggestions_list.clear()
            for anchor in matches:
                anchor_id = anchor.get("id", "")
                anchor_text = anchor.get("text", "")
                item = QListWidgetItem(f"#{anchor_id} ({anchor_text})")
                item.setData(Qt.ItemDataRole.UserRole, "#" + anchor_id)
                self.suggestions_list.addItem(item)
        
            self.suggestions_list.setVisible(True)
            return

        # Поиск по страницам (с @ или без)
        stripped = text.lstrip("@").lower()
        if len(stripped) < 2:
            self.suggestions_list.setVisible(False)
            return

        matches = []
        for page_id, display_name in READY_PAGES.items():
            if stripped in page_id.lower() or text in display_name.lower():
                matches.append((page_id, display_name))

        if not matches:
            self.suggestions_list.setVisible(False)
            return

        matches = matches[:5]

        self.suggestions_list.clear()
        for page_id, display_name in matches:
            item = QListWidgetItem(f"{display_name} (@{page_id})")
            item.setData(Qt.ItemDataRole.UserRole, page_id)
            self.suggestions_list.addItem(item)

        self.suggestions_list.setVisible(True)

    def _on_suggestion_clicked(self, item):
        """Пользователь выбрал страницу из подсказок"""
        page_id = item.data(Qt.ItemDataRole.UserRole)
        if not page_id:
            return

        # Для якоря - значение уже имеет '#'
        if page_id.startswith("#"):
            self.url_input.setText(page_id)
        else: # Страница
            # Устанавливаем URL как @PageId
            self.url_input.setText(f"@{page_id}")

            # Если поле текста пустое - заполняем русским названием
            if not self.text_input.text().strip() and not self.text_input.isReadOnly():
                display_name = READY_PAGES.get(page_id, page_id)
                self.text_input.setText(display_name)

        self.suggestions_list.setVisible(False)