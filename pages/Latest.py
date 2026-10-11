# LatestPage
from PyQt5.QtCore import Qt, pyqtSignal, QTimer, QSize
from PyQt5.QtWidgets import *
from PyQt5.QtGui import QIcon
import os

from .Base import BasePage
from .Base import ImageLoader
from .Base import get_page_preview
from .Base import history_manager
from .Base import saved_manager
from .Wiki import WikiPage

class LatestPage(BasePage):
    # Сигнал для перехода на страницу
    page_opened = pyqtSignal(str)

    def __init__(self, parent=None):
        super().__init__(parent)

        self.add_title("История просмотра")
        self.history_manager = history_manager

        # Создаем метку
        self.image_label = QLabel("Загрузка...")
        self.image_label.setObjectName("pageLogo")
        self.image_label.setAlignment(Qt.AlignRight | Qt.AlignTop)

        self.description_label = QLabel("Недавно просмотренные страницы") # Создаем описание раздела
        self.description_label.setObjectName("pageDescription")
        self.description_label.setAlignment(Qt.AlignLeft | Qt.AlignVCenter)

        self.settings_button = QPushButton("Настройки")
        self.settings_button.setObjectName("settingsButton")
        self.settings_button.clicked.connect(self.show_settings)
    
        # Крепим виджеты
        Hlayout = QHBoxLayout()
        Hlayout.addWidget(self.description_label)
        Hlayout.addStretch()
        Hlayout.addWidget(self.settings_button, alignment=Qt.AlignRight | Qt.AlignBottom)
        Hlayout.addWidget(self.image_label, alignment= Qt.AlignRight | Qt.AlignTop)
        Hlayout.setContentsMargins(0,0,0,0)

        # Крепим к основному лайауту
        self.layout.addLayout(Hlayout)
        

        # Запуск загрузки картинки в отдельном потоке
        self.loader = ImageLoader()
        self.loader.finished.connect(self.on_image_loaded)
        self.loader.error.connect(self.on_image_error)
        self.loader.start()

        # Добавляем разделитель
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

        # Подключаем сигналы
        self.history_manager.history_changed.connect(self.update_cards)
        self.scroll_area.installEventFilter(self)

        # Обновляем карточки через 100 мс
        QTimer.singleShot(100, self.update_cards)

    def on_image_loaded(self, pixmap):
        """Вызывается, когда картинка успешно загружена"""
        self.image_label.setPixmap(pixmap)
        self.image_label.setText("") # Убираем текст "Загрузка"
        if not self.history_manager.recent_pages:
            self.update_cards()

    def on_image_error(self):
        """Вызывается при ошибке"""
        self.image_label.setText("Ошибка загрузки")
        self.image_label.setStyleSheet("color: red;")

    def show_settings(self):
        """Показывает диалог настроек"""
        dialog = SettingsDialog(self.history_manager, self)

        # Если пользователь нажал "Сохранить"
        if dialog.exec_() == QDialog.Accepted: # Показывает модальное окно и ждет закрытия
            settings = dialog.get_settings()
            self.history_manager.update_settings( # Обновляем настройки
                settings["save_history"],
                settings["limit"]
            )

    def update_cards(self):
        """Обновляет отображение карточек"""
        # Очищаем старые карточки

        while self.grid_layout.count():
            item = self.grid_layout.takeAt(0)
            if item.widget():
                item.widget().deleteLater()

        # Получаем список недавних страниц
        recent_pages = self.history_manager.recent_pages

        # Если история пуста
        if not recent_pages:
            empty_widget = self._make_empty_widget(
                "История пуста.\nПросматривайте страницы, и они появятся здесь.",
                self.image_label.pixmap(),
                (250, 125)
            )
            self.grid_layout.addWidget(empty_widget, 0, 0, 1, 1, Qt.AlignCenter)
            return

        # Получаем ширину области для карточек
        available_width = self.scroll_area.viewport().width()

        # Ширина карточки + отступ
        card_width = 250
        spacing = 10

        # Вычисляем кол-во колонок
        columns = max(1, (available_width + spacing) // (card_width + spacing))

        # Создаем карточки
        for i, page_id in enumerate(recent_pages):
            # Получаем заголовок и превью
            title = page_id
            preview = get_page_preview(page_id)

            # Создаем карточку
            card = PreviewCard(page_id, title, preview)
            card.clicked.connect(self.on_card_clicked)

            # Вычисляем позицию в стеке
            row = i // columns
            col = i % columns

            self.grid_layout.addWidget(card, row, col)

        self.grid_layout.setAlignment(Qt.AlignCenter)

    def on_card_clicked(self, page_id):
        """Обработка клика по карточке"""
        # Отправляем сигнал для перехода
        self.page_opened.emit(page_id)

    def resizeEvent(self, event):
        """Вызывается при изменении размера окна"""
        super().resizeEvent(event)
        # Пересчитываем карточки при изменении размера
        QTimer.singleShot(50, self.update_cards)

class PreviewCard(QFrame):
    """Карточка для отображения страницы в истории"""

    # Сигнал с ID страницы (будет срабатывать при клике)
    clicked = pyqtSignal(str)
    remove_requested = pyqtSignal(str)

    def __init__(self, page_id, title, preview_text, removable=False, parent=None):
        super().__init__(parent)

        self.setObjectName("previewCard")

        # Сохраняем ID страницы
        self.page_id = page_id
        self.removable = removable

        # Фиксированный размер карточки
        self.setFixedSize(250, 195)

        # Создаем основной layout
        layout = QVBoxLayout(self)
        layout.setContentsMargins(10, 10, 10, 10) # Отступы внутри самой карточки
        layout.setSpacing(5) # Расстояние между карточками

        # Заголовок (название страницы)
        self.title_label = QLabel(title)
        self.title_label.setObjectName("cardTitle")
        self.title_label.setWordWrap(True)

        # Превью текста со страницы
        self.preview_label = QLabel(preview_text)
        self.preview_label.setObjectName("cardPreview")
        self.preview_label.setWordWrap(True)
        self.preview_label.setTextInteractionFlags(Qt.NoTextInteraction)

        # Если removable - оставляем снизу место под звездочку
        if self.removable:
            self.preview_label.setContentsMargins(0, 0, 0, 0)

        # Крепим к лайауту
        layout.addWidget(self.title_label)
        layout.addWidget(self.preview_label)
        layout.addStretch()

        # Кнопка-звездочка
        if self.removable:
            self.remove_btn = QPushButton(self)
            self.remove_btn.setObjectName("cardRemoveBtn")
            self.remove_btn.setFixedSize(24, 24)
            self.remove_btn.setCursor(Qt.PointingHandCursor)

            # Иконка звездочки
            icon_path = os.path.join(
                os.path.dirname(os.path.abspath(__file__)),
                "WikiContent", "WikiImages", "red_saved_icon.png"
            )
            self.remove_btn.setIcon(QIcon(icon_path))
            self.remove_btn.setIconSize(QSize(32, 32))

            self.remove_btn.clicked.connect(self._on_remove_clicked)

            # Ставим кнопку в правый нижний угол карточки (absolute)
            self.remove_btn.move(self.width() - 30, self.height() - 30)

    def mousePressEvent(self, event):
        """Обработка клика по карточке"""
        if event.button() == Qt.LeftButton:
            self.clicked.emit(self.page_id) # Подаем сигнал clicked с ID страницы

    def _on_remove_clicked(self):
        """Клик по звёздочке - не открывать страницу, а запросить удаление"""
        self.remove_requested.emit(self.page_id)

class SettingsDialog(QDialog):
    """Диалог настроек истории"""

    def __init__(self, history_manager, parent=None):
        super().__init__(parent)

        # Создаем экземпляр класса для получения кол-ва имеющихся страниц | Увы, может быть избыточным
        self.pages_count = WikiPage()

        # Сохраняем ссылку на менеджер
        self.history_manager = history_manager

        # Настройки окна
        self.setWindowTitle("Настройки истории")
        self.setFixedSize(250, 125)

        # Чекбокс сохранения истории
        self.save_checkbox = QCheckBox("Сохранять историю просмотра")
        self.save_checkbox.setObjectName("settingsCheckbox")
        self.save_checkbox.setChecked(history_manager.settings["save_history"]) # Устанавливаем значение из настроек

        # Поле для лимита
        limit_layout = QHBoxLayout()
        limit_label = QLabel("Лимит сохраненных страниц")

        self.limit_spinbox = QSpinBox()
        self.limit_spinbox.setObjectName("settingsSpinbox")
        self.limit_spinbox.setRange(1, self.pages_count.send_pages_count()) # Устанавливаем диапазон
        self.limit_spinbox.setValue(history_manager.settings["limit"]) # Устанавлием значение из настроек

        limit_layout.addWidget(limit_label)
        limit_layout.addWidget(self.limit_spinbox)
        limit_layout.addStretch()

        # Кнопки
        buttons_layout = QHBoxLayout()
        self.save_button = QPushButton("Сохранить")
        self.save_button.setObjectName("settingsSaveBtn")
        self.cancel_button = QPushButton("Отмена")
        self.cancel_button.setObjectName("settingsCancelBtn")

        # Подключаем их
        self.save_button.clicked.connect(self.accept) # Закрыть с "ОК"
        self.cancel_button.clicked.connect(self.reject) # Закрыть с "Отмена"

        buttons_layout.addStretch()
        buttons_layout.addWidget(self.save_button)
        buttons_layout.addWidget(self.cancel_button)

        # Сборка layout
        layout = QVBoxLayout(self)
        layout.addWidget(self.save_checkbox)
        layout.addLayout(limit_layout)
        layout.addStretch()
        layout.addLayout(buttons_layout)

    def get_settings(self):
        """Метод возврата настроек из диалога"""
        return {
            "save_history": self.save_checkbox.isChecked(),
            "limit": self.limit_spinbox.value()
        }