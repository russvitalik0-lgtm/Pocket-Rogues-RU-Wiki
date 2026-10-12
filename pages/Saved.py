# SavedPage
from PyQt6.QtCore import Qt, pyqtSignal, QTimer
from PyQt6.QtWidgets import *
from .Base import BasePage
from .Base import ImageLoader
from .Base import get_page_preview
from .Base import saved_manager
from .Latest import PreviewCard


class SavedPage(BasePage):
    # Сигнал для перехода на страницу
    page_opened = pyqtSignal(str)

    def __init__(self, parent=None):
        super().__init__(parent)

        self.add_title("Сохранённые страницы")
        self.saved_manager = saved_manager

        # Метка для картинки
        self.image_label = QLabel("Загрузка...")
        self.image_label.setObjectName("pageLogo")
        self.image_label.setAlignment(Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignTop)

        # Описание раздела
        self.description_label = QLabel("Страницы, которые вы сохранили")
        self.description_label.setObjectName("pageDescription")
        self.description_label.setAlignment(Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignVCenter)

        # Крепим виджеты
        Hlayout = QHBoxLayout()
        Hlayout.addWidget(self.description_label)
        Hlayout.addStretch()
        Hlayout.addWidget(self.image_label, alignment=Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignTop)
        Hlayout.setContentsMargins(0, 0, 0, 0)

        self.layout.addLayout(Hlayout)

        # Запуск загрузки картинки
        self.loader = ImageLoader()
        self.loader.finished.connect(self.on_image_loaded)
        self.loader.error.connect(self.on_image_error)
        self.loader.start()

        # Разделитель
        self.add_separator()

        # Контейнер карточек
        self.cards_widget = QWidget()
        self.cards_widget.setObjectName("cardsContainer")
        self.grid_layout = QGridLayout(self.cards_widget)
        self.grid_layout.setSpacing(10)
        self.grid_layout.setContentsMargins(0, 10, 0, 10)

        # Область прокрутки
        self.scroll_area = QScrollArea()
        self.scroll_area.setObjectName("pageScrollArea")
        self.scroll_area.setWidgetResizable(True)
        self.scroll_area.setWidget(self.cards_widget)

        self.layout.addWidget(self.scroll_area, 1)

        # Подключаем сигнал менеджера
        self.saved_manager.saved_changed.connect(self.update_cards)

        # Обновляем карточки через 100 мс (после полной инициализации UI)
        QTimer.singleShot(100, self.update_cards)

    def on_image_loaded(self, pixmap):
        """Вызывается, когда картинка успешно загружена"""
        self.image_label.setPixmap(pixmap)
        self.image_label.setText("")
        if not self.saved_manager.saved_pages:
            self.update_cards()

    def on_image_error(self):
        """Вызывается при ошибке"""
        self.image_label.setText("Ошибка загрузки")
        self.image_label.setStyleSheet("color: red;")

    def update_cards(self):
        """Обновляет отображение карточек"""
        # Очищаем старые карточки
        while self.grid_layout.count():
            item = self.grid_layout.takeAt(0)
            if item.widget():
                item.widget().deleteLater()

        # Получаем список сохранённых страниц
        saved_pages = self.saved_manager.saved_pages

        if not saved_pages:
            empty_widget = self._make_empty_widget(
                "Список пуст.\nСохраняйте страницы кнопкой-звёздочкой слева, и они появятся здесь.",
                self.image_label.pixmap(),
                (250, 125)
            )
            self.grid_layout.addWidget(empty_widget, 0, 0, 1, 1, Qt.AlignmentFlag.AlignCenter)
            return

        # Вычисляем кол-во колонок
        available_width = self.scroll_area.viewport().width()
        card_width = 225
        spacing = 10
        columns = max(1, (available_width + spacing) // (card_width + spacing))

        # Создаём карточки
        for i, page_id in enumerate(saved_pages):
            title = page_id
            preview = get_page_preview(page_id)

            # removable=True - показываем звёздочку для удаления
            card = PreviewCard(page_id, title, preview, removable=True)

            card.clicked.connect(self.on_card_clicked)
            card.remove_requested.connect(self.on_card_remove)

            row = i // columns
            col = i % columns

            self.grid_layout.addWidget(card, row, col)

        self.grid_layout.setAlignment(Qt.AlignmentFlag.AlignCenter)

    def on_card_clicked(self, page_id):
        """Обработка клика по карточке"""
        self.page_opened.emit(page_id)

    def on_card_remove(self, page_id):
        """Обработка удаления из сохранённых"""
        self.saved_manager.remove_page(page_id)

    def resizeEvent(self, event):
        """Пересчитываем карточки при изменении размера"""
        super().resizeEvent(event)
        QTimer.singleShot(50, self.update_cards)