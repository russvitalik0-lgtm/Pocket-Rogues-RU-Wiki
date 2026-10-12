# StylePage
from PyQt6.QtCore import Qt, pyqtSignal, QTimer
from PyQt6.QtWidgets import *

from .Base import BasePage
from .Base import ImageLoader
from .theme_manager import ThemeManager

class StylePage(BasePage):
    """Страница выбора темы стилизации приложения"""

    def __init__(self, theme_manager, parent=None):
        super().__init__(parent)

        self.theme_manager = theme_manager

        self.add_title("Стилизация")
        self.description_label = QLabel("Выберите тему оформления приложения\nМожете опираться на миниатюры доступных тем стилизации")
        self.description_label.setObjectName("pageDescription")

        # Логотип справа сверху (подобно другим страницам)
        self.image_label = QLabel("Загрузка...")
        self.image_label.setObjectName("pageLogo")
        self.image_label.setAlignment(
            Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignTop
        )

        # Размещаем
        Hlayout = QHBoxLayout()
        Hlayout.addWidget(self.description_label, alignment = Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignVCenter)
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

        # Контейнер карточек
        self.cards_widget = QWidget()
        self.cards_widget.setObjectName("cardsContainer")
        self.grid_layout = QGridLayout(self.cards_widget)
        self.grid_layout.setSpacing(20)
        self.grid_layout.setContentsMargins(0, 10, 0, 10)

        # Область прокрутки
        self.scroll_area = QScrollArea()
        self.scroll_area.setObjectName("pageScrollArea")
        self.scroll_area.setWidgetResizable(True)
        self.scroll_area.setWidget(self.cards_widget)

        self.layout.addWidget(self.scroll_area, 1)

        # Обновляем карточки при смене темы (например, если тему поменяли в другом месте)
        self.theme_manager.theme_changed.connect(self.update_cards)

        # Первичная отрисовка
        QTimer.singleShot(100, self.update_cards)

    def on_image_loaded(self, pixmap):
        """Вызывается, когда картинка успешно загружена"""
        self.image_label.setPixmap(pixmap)
        self.image_label.setText("") # Убираем текст "Загрузка"
    
    def on_image_error(self):
        """Вызывается при ошибке"""
        self.image_label.setText("Ошибка загрузки")
        self.image_label.setStyleSheet("color: red;")

    def update_cards(self):
        """Пересобирает галерею карточек тем"""
        # Очищаем старые карточки
        while self.grid_layout.count():
            item = self.grid_layout.takeAt(0)
            if item.widget():
                item.widget().deleteLater()

        # Ширина карточки + отступ
        card_width = 400
        spacing = 20

        # Вычисляем кол-во колонок
        available_width = self.scroll_area.viewport().width()
        columns = max(1, (available_width + spacing) // (card_width + spacing))

        # Создаём карточку для каждой темы
        for i, theme_name in enumerate(ThemeManager.AVAILABLE_THEMES):
            palette = ThemeManager.THEME_PALETTES.get(theme_name)
            if not palette:
                continue

            card = self._make_theme_card(theme_name, palette)

            row = i // columns
            col = i % columns
            self.grid_layout.addWidget(card, row, col, alignment=Qt.AlignmentFlag.AlignCenter)

        self.grid_layout.setAlignment(Qt.AlignmentFlag.AlignCenter)


    def resizeEvent(self, event):
        """Пересчитываем кол-во колонок при изменении размера окна"""
        super().resizeEvent(event)
        QTimer.singleShot(50, self.update_cards)

    def _make_theme_card(self, theme_name, palette):
        """Создаёт карточку превью для одной темы
        theme_name - ID темы ('light', 'dark')
        palette - словарь с цветами (из ThemeManager.THEME_PALLETS)
        """
        # Корневой фрейм карточки (400x260, чтобы влезли все элементы)
        card = QFrame()
        card.setObjectName("themeCard")
        card.setFixedSize(400, 260)
        card.setCursor(Qt.CursorShape.PointingHandCursor)

        # Вертикальный layout: Titlebar сверху, содержимое в середине, название - снизу
        card_layout = QVBoxLayout(card)
        card_layout.setContentsMargins(0, 0, 0, 0) # Без отступов
        card_layout.setSpacing(0) # Без spacing

        # TitleBar - имитация заголовка окна
        titlebar = QFrame()
        titlebar.setFixedHeight(22)
        titlebar.setStyleSheet(f"background-color: {palette['bg_panel']}; border: none;")

        titlebar_layout = QHBoxLayout(titlebar)
        titlebar_layout.setContentsMargins(8, 0, 8, 0)
        titlebar_layout.setSpacing(0)

        # Название окна слева
        title_text = QLabel("Pocket Rogues RU-Wiki")
        title_text.setStyleSheet(f"color: {palette['text']}; font-size: 10px; background: transparent;")
        titlebar_layout.addWidget(title_text)

        titlebar_layout.addStretch()

        # Имитация трёх кнопок окна справа
        for symbol in ["─", "□", "✕"]:
            btn = QLabel(symbol)
            btn.setStyleSheet(f"color: {palette['text']}; font-size: 10px; background: transparent; padding: 0 4px;")
            titlebar_layout.addWidget(btn)

        card_layout.addWidget(titlebar)

        """Нижняя часть: слева список вкладок, справа контент"""
        body = QWidget()
        body_layout = QHBoxLayout(body)
        body_layout.setContentsMargins(0, 0, 0, 0)
        body_layout.setSpacing(0)

        # Левая панель - имитация списка вкладок
        left = QFrame()
        left.setFixedWidth(100)
        left.setStyleSheet(f"background-color: {palette['bg_list']}; border: none;")

        left_layout = QVBoxLayout(left)
        left_layout.setContentsMargins(6, 8, 6, 8)
        left_layout.setSpacing(4)

        # Четыре пункта; первый - активный (с accent-полосой)
        for idx, tab_text in enumerate(["Википедия", "Недавние", "Сохранённое", "Заметки", "Стилизация"]):
            tab = QLabel(tab_text)
            tab.setFixedHeight(20)
            tab.setContentsMargins(6, 0, 0, 0)

            if idx == 0:
                # Активная вкладка - accent-полоса слева через border-left
                tab.setStyleSheet(
                    f"color: {palette['text_heading']}; font-size: 9px; "
                    f"background-color: {palette['bg_panel']}; "
                    f"border-left: 3px solid {palette['accent']}; "
                    f"padding-left: 4px;"
                )
            else:
                # Обычная вкладка - просто фон списка
                tab.setStyleSheet(
                    f"color:{palette['text']}; font-size: 9px; "
                    f"background-color: transparent; padding-left: 7px;"
                )

            left_layout.addWidget(tab)

        left_layout.addStretch()
        body_layout.addWidget(left)

        # Правая панель - имитация контента страницы
        right = QFrame()
        right.setStyleSheet(f"background-color: {palette['bg_window']}; border: none;")

        right_layout = QVBoxLayout(right)
        right_layout.setContentsMargins(20, 15, 20, 15)
        right_layout.setSpacing(8)

        # Заголовок страницы
        page_title = QLabel("Заголовок страницы")
        page_title.setStyleSheet(
            f"color: {palette['text_heading']}; font-size: 14px;"
        )
        right_layout.addWidget(page_title)

        # Accent-линия под заголовком (разделитель)
        accent_line = QFrame()
        accent_line.setFixedHeight(2)
        accent_line.setStyleSheet(
            f"background-color: {palette['accent']}; border: none;"
        )
        right_layout.addWidget(accent_line)

        # Пара строк обычного текста
        body_text = QLabel("Это обычный текст в цвете темы.\nОн показывает, как читается контент")
        body_text.setStyleSheet(
            f"color: {palette['text']}; font-size: 10px; background: transparent;"
        )
        body_text.setWordWrap(True)
        right_layout.addWidget(body_text)

        right_layout.addStretch()

        # Accent-кнопка внизу
        accent_btn = QLabel("Кнопка")
        accent_btn.setFixedSize(70, 22)
        accent_btn.setAlignment(Qt.AlignmentFlag.AlignCenter)
        accent_btn.setStyleSheet(
            f"background-color: {palette['accent']}; color: #ffffff; "
            f"font-size: 10px; border-radius: 3px;"
        )
        right_layout.addWidget(accent_btn)

        body_layout.addWidget(right, 1)
        card_layout.addWidget(body, 1)

        # Название темы под карточкой
        theme_label = QLabel(palette.get("display_name", theme_name))
        theme_label.setFixedHeight(28)
        theme_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        theme_label.setStyleSheet(
            f"color: {palette['text']}; font-size: 12px; "
            f"font-weight: bold; background: transparent;"
        )
        card_layout.addWidget(theme_label)

        # Рамка карточки - accent, если тема активна, иначе - border
        is_active = (theme_name == self.theme_manager.current_theme)
        border_color = palette['accent'] if is_active else palette['border']
        border_width = 2

        card.setStyleSheet(
            f"#themeCard {{ "
            f" background-color: {palette['bg_window']}; "
            f" border: {border_width}px solid {border_color}; "
            f" border-radius: 6px; "
            f"}}"
        )

        # Клик по карточке применяет тему
        card.mousePressEvent = lambda event, name=theme_name: self._on_card_clicked(event, name)

        return card

    def _on_card_clicked(self, event, theme_name):
        """Клик по карточке - выбранная тема"""
        if event.button() == Qt.MouseButton.LeftButton:
            self.theme_manager.apply_theme(theme_name)