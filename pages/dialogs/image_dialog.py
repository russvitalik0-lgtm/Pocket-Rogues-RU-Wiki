# ImageDialog
from PyQt6.QtWidgets import *
from PyQt6.QtCore import Qt, QSize
from PyQt6.QtGui import QIcon, QPixmap
from pathlib import Path

WIKI_IMAGES_DIR = Path(__file__).parent.parent / "WikiContent" / "WikiImages"

class ImageDialog(QDialog):
    """Диалог вставки изображения в VE"""

    def __init__(self, parent=None):
        super().__init__(parent)

        self.setWindowTitle("Media settings")
        self.setMinimumSize(715, 500)

        # Основной layout
        layout = QVBoxLayout(self)

        # Стек страниц
        self.stack = QStackedWidget()
        layout.addWidget(self.stack)

        # Страница 1: галерея и импорт
        self.tab = QTabWidget()
        self.gallery_page = QWidget()
        self.import_page = QWidget()
        self.tab.addTab(self.gallery_page, "Галерея")
        self.tab.addTab(self.import_page, "Импорт")
        self.stack.addWidget(self.tab)

        # Страница 2: предпросмотр и информация
        self.preview_page = QWidget()
        self.stack.addWidget(self.preview_page)

        # Страница 3: редактор
        self.editor_page = QWidget()
        self.stack.addWidget(self.editor_page)

        # Панель кнопок
        buttons_layout = QHBoxLayout()

        self.back_btn = QPushButton("← Back")
        self.back_btn.clicked.connect(self._on_back)
        buttons_layout.addWidget(self.back_btn)

        buttons_layout.addStretch()

        self.use_btn = QPushButton("Use this image")
        self.use_btn.clicked.connect(self._on_use_this_image)
        buttons_layout.addWidget(self.use_btn)

        self.insert_btn = QPushButton("Insert")
        self.insert_btn.clicked.connect(self._on_insert)
        buttons_layout.addWidget(self.insert_btn)

        self.cancel_btn = QPushButton("Cancel")
        self.cancel_btn.clicked.connect(self.reject)
        buttons_layout.addWidget(self.cancel_btn)

        layout.addLayout(buttons_layout)

        # Заполнение страниц
        self._build_gallery_page()
        self._build_import_page()
        self._build_preview_page()
        self._build_editor_page()

        # Изначальные индексы
        self.tab.setCurrentIndex(0)
        self.stack.setCurrentIndex(0)
        self._update_buttons_for_page(0)

        # Выбранный файл
        self.selected_file = None

    # ----- Галерея -----

    def _build_gallery_page(self):
        """Первая вкладка страницы: Галерея + сетка превью"""
        layout = QVBoxLayout(self.gallery_page)

        # Поле поиска
        self.search_input = QLineEdit()
        self.search_input.setPlaceholderText("Поиск по имени файла...")
        self.search_input.textChanged.connect(self._filter_gallery)
        layout.addWidget(self.search_input)

        # Сетка превью (QListWidget в режиме IconMode)
        self.gallery_list = QListWidget()
        self.gallery_list.setViewMode(QListWidget.ViewMode.IconMode)
        self.gallery_list.setIconSize(QSize(100, 100))
        self.gallery_list.setGridSize(QSize(130, 160))
        self.gallery_list.setResizeMode(QListWidget.ResizeMode.Adjust)
        self.gallery_list.setMovement(QListWidget.Movement.Static)
        self.gallery_list.setSpacing(8)
        self.gallery_list.setWordWrap(True)
        self.gallery_list.itemClicked.connect(self._on_gallery_item_clicked)
        layout.addWidget(self.gallery_list, 1)

        # Загружаем файлы
        self._load_gallery_files()

    def _load_gallery_files(self):
        """Загружает список файлов из WikiImages/ в галерею"""
        if not WIKI_IMAGES_DIR.exists():
            return

        # Допустимые расширения изображений
        extensions = {".png", ".jpg", ".jpeg", ".gif", ".webp", ".bmp"}

        self.gallery_list.clear()

        for file_path in sorted(WIKI_IMAGES_DIR.iterdir()):
            if not file_path.is_file():
                continue
            if file_path.suffix.lower() not in extensions:
                continue

            # Создаем иконку с превью
            pixmap = QPixmap(str(file_path))
            if pixmap.isNull():
                continue

            # Создаем миниатюру
            thumbnail = pixmap.scaled(
                100, 100,
                Qt.AspectRatioMode.KeepAspectRatio,
                Qt.TransformationMode.SmoothTransformation
            )

            item = QListWidgetItem(QIcon(thumbnail), file_path.name)
            item.setData(Qt.ItemDataRole.UserRole, file_path.name)
            item.setToolTip(file_path.name)
            self.gallery_list.addItem(item)

    def _filter_gallery(self, text):
        """Фильтрует галерею по введенному тексту"""
        text = text.strip().lower()
        for i in range(self.gallery_list.count()):
            item = self.gallery_list.item(i)
            file_name = item.data(Qt.ItemDataRole.UserRole) or ""
            item.setHidden(text not in file_name.lower())

    def _on_gallery_item_clicked(self, item):
        """Пользователь выбрал файл из галереи"""
        file_name = item.data(Qt.ItemDataRole.UserRole)
        if not file_name:
            return

        self.selected_file = file_name

        # Обновляем предпросмотр и переходим на страницу предпросмотра
        self._update_preview(file_name)
        self.stack.setCurrentIndex(1)
        self._update_buttons_for_page(1)

    # ----- Импорт -----

    def _build_import_page(self):
        """Вторая вкладка страницы: Импорт своих изображений в определенном формате (TODO)"""
        layout = QVBoxLayout(self.import_page)
        label = QLabel("Импорт изображений в разработке...")
        layout.setAlignment(Qt.AlignmentFlag.AlignCenter)
        label.setStyleSheet("color: #888; font-size: 14px;")
        layout.addWidget(label)

    # ----- Превью -----

    def _build_preview_page(self):
        """Страница предпросмотра: большая картинка + информация"""
        layout = QVBoxLayout(self.preview_page)

        # Превью картинки
        self.preview_image_label = QLabel()
        self.preview_image_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.preview_image_label.setMinimumHeight(300)
        self.preview_image_label.setStyleSheet("background-color: #1a1a1a; border: 1px solid #333;")
        layout.addWidget(self.preview_image_label, 1)

        # Информация о файле
        info_layout = QVBoxLayout()

        self.preview_filename_label = QLabel()
        self.preview_filename_label.setStyleSheet("font-size: 16px; font-weight: bold; color: #ffffff;")
        info_layout.addWidget(self.preview_filename_label)

        self.preview_details_label = QLabel()
        self.preview_details_label.setStyleSheet("color: #888; font-size: 12px;")
        info_layout.addWidget(self.preview_details_label)

        layout.addLayout(info_layout)

    def _update_preview(self, file_name):
        """Обновляет страницу предпросмотра"""
        file_path = WIKI_IMAGES_DIR / file_name

        if not file_path.exists():
            self.preview_image_label.setText("Файл не найден")
            self.preview_filename_label.setText(file_name)
            self.preview_details_label.setText("")
            return

        # Большое превью
        pixmap = QPixmap(str(file_path))
        original_width = pixmap.width()
        original_height = pixmap.height()
        if pixmap.isNull():
            self.preview_image_label.setText("Не удалось загрузить изображение")
        else:
            # Ограничиваем размер, чтобы влезло в диалог
            max_width = 600
            max_height = 400
            if pixmap.width() > max_width or pixmap.height() > max_height:
                pixmap = pixmap.scaled(
                    max_width, max_height,
                    Qt.AspectRatioMode.KeepAspectRatio,
                    Qt.TransformationMode.SmoothTransformation
                )
            self.preview_image_label.setPixmap(pixmap)

        # Имя файла
        self.preview_filename_label.setText(file_name)

        # Размер в пикселях и формат
        fmt = file_path.suffix[1:].upper() # "PNG" вместе ".png"

        # Размер файла
        size_bytes = file_path.stat().st_size
        if size_bytes < 1024:
            size_str = f"{size_bytes} Б"
        elif size_bytes < 1024 * 1024:
            size_str = f"{size_bytes / 1024:.1f} КБ"
        else:
            size_str = f"{size_bytes / (1024 * 1024):.1f} МБ"

        # Собираем строку
        details = f"{original_width} x {original_height} px • {fmt} • {size_str}"
        self.preview_details_label.setText(details)

    # ----- Редактор -----

    def _build_editor_page(self):
        """Страница редактора: General + Advanced"""
        layout = QVBoxLayout(self.editor_page)

        # QTabWidget
        self.editor_tabs = QTabWidget()
        layout.addWidget(self.editor_tabs, 1)

        # Вкладка General
        general_tab = QWidget()
        self._build_general_tab(general_tab)
        self.editor_tabs.addTab(general_tab, "General")

        # Вкладка Advanced
        advanced_tab = QWidget()
        self._build_advanced_tab(advanced_tab)
        self.editor_tabs.addTab(advanced_tab, "Advanced")

        # Кнопка Change Image
        change_layout = QHBoxLayout()
        self.change_image_btn = QPushButton("Change Image")
        self.change_image_btn.clicked.connect(self._on_change_image)
        change_layout.addWidget(self.change_image_btn)
        change_layout.addStretch()
        layout.addLayout(change_layout)

    def _build_general_tab(self, widget):
        """Вкладка General: имя файла, caption, alt-текст"""
        layout = QVBoxLayout(widget)

        # Имя файла
        self.file_name_label = QLabel()
        self.file_name_label.setStyleSheet("font-size: 14px; font-weight: bold; color: #ffffff;")
        layout.addWidget(self.file_name_label)
        layout.addSpacing(15)

        # Caption
        caption_label = QLabel("Caption")
        caption_label.setStyleSheet("font-weight: bold;")
        caption_label.setToolTip("Текст под изображением")
        layout.addWidget(caption_label)

        self.caption_edit = QPlainTextEdit()
        self.caption_edit.setPlaceholderText("Текст, отображающийся рядом с изображением")
        self.caption_edit.setMaximumHeight(100)
        layout.addWidget(self.caption_edit)

        # Alternative text
        alt_label = QLabel("Alternative text")
        alt_label.setStyleSheet("font-weight: bold;")
        alt_label.setToolTip("Текст-заглушка, если изображение не появилось")
        layout.addWidget(alt_label)

        self.alt_input = QLineEdit()
        self.alt_input.setPlaceholderText("Текст, видимый если картинка не загрузилась")
        layout.addWidget(self.alt_input)

        layout.addStretch()

    def _build_advanced_tab(self, widget):
        """Вкладка Advanced: позиция, тип и размер"""
        layout = QVBoxLayout(widget)

        # Position
        pos_label = QLabel("Position")
        pos_label.setStyleSheet("font-weight: bold;")
        layout.addWidget(pos_label)

        self.wrap_checkbox = QCheckBox("Wrap text around this item")
        self.wrap_checkbox.setChecked(True)
        self.wrap_checkbox.setToolTip("Если выключено: изображение 'загораживает' текст, находясь поверх него. Если включено: текст обтекает изображение.")
        self.wrap_checkbox.toggled.connect(self._update_position_radios)
        layout.addWidget(self.wrap_checkbox)

        # Радио-кнопки позиции
        pos_layout = QHBoxLayout()
        self.pos_group = QButtonGroup(self)

        self.pos_left = QRadioButton("Left")
        self.pos_center = QRadioButton("Center")
        self.pos_right = QRadioButton("Right")
        self.pos_right.setChecked(True) # Стандарт: позиционирование по правому краю

        self.pos_group.addButton(self.pos_left, 0)
        self.pos_group.addButton(self.pos_center, 1)
        self.pos_group.addButton(self.pos_right, 2)

        pos_layout.addWidget(self.pos_left)
        pos_layout.addWidget(self.pos_center)
        pos_layout.addWidget(self.pos_right)
        pos_layout.addStretch()
        layout.addLayout(pos_layout)

        layout.addSpacing(15)

        # Image type
        type_label = QLabel("Image type")
        type_label.setStyleSheet("font-weight: bold;")
        layout.addWidget(type_label)

        self.type_combo = QComboBox()
        self.type_combo.addItems(["Thumbnail", "Frameless", "Frame", "Basic"])
        self.type_combo.setToolTip("Стиль рамки изображения")
        layout.addWidget(self.type_combo)

        # Border
        self.border_checkbox = QCheckBox("Border")
        layout.addWidget(self.border_checkbox)

        layout.addSpacing(15)

        # Image size
        size_label = QLabel("Image size")
        size_label.setStyleSheet("font-weight: bold;")
        layout.addWidget(size_label)

        self.size_default_radio = QRadioButton("Default") # Стандарт: базовый размер картинки
        self.size_custom_radio = QRadioButton("Custom")
        self.size_default_radio.setChecked(True)

        size_radio_layout = QHBoxLayout()
        size_radio_layout.addWidget(self.size_default_radio)
        size_radio_layout.addWidget(self.size_custom_radio)
        size_radio_layout.addStretch()
        layout.addLayout(size_radio_layout)

        # Custom size (spinboxes)
        custom_size_layout = QHBoxLayout()

        self.width_spin = QSpinBox()
        self.width_spin.setRange(8, 2048)
        self.width_spin.setValue(32)
        self.width_spin.setSuffix(" px")

        self.height_spin = QSpinBox()
        self.height_spin.setRange(8, 2048)
        self.height_spin.setValue(32)
        self.height_spin.setSuffix(" px")

        custom_size_layout.addWidget(self.width_spin)
        custom_size_layout.addWidget(QLabel("x"))
        custom_size_layout.addWidget(self.height_spin)
        custom_size_layout.addStretch()
        layout.addLayout(custom_size_layout)

        # Включаем/выключаем spinbox в зависимости от выбора
        self.size_default_radio.toggled.connect(self._update_size_inputs)
        self.size_custom_radio.toggled.connect(self._update_size_inputs)

        self.width_spin.setEnabled(False) # ──┬ Изначально - disabled
        self.height_spin.setEnabled(False) # ─┘

        layout.addStretch()

    def _on_change_image(self):
        """Возврат на галерею для выбора другой картинки"""
        self.stack.setCurrentIndex(0)
        self._update_buttons_for_page(0)

    def _update_position_radios(self, enabled):
        """Изменяет состояние радио позиции при изменении wrap-checkbox"""
        self.pos_left.setEnabled(enabled)
        self.pos_center.setEnabled(enabled)
        self.pos_right.setEnabled(enabled)

    def _update_size_inputs(self):
        """Изменяет состояние spinbox размера в зависимости от Default/Custom"""
        custom = self.size_custom_radio.isChecked()
        self.width_spin.setEnabled(custom)
        self.height_spin.setEnabled(custom)

    def _update_editor(self, file_name):
        """Заполняет редактор данными выбранного файла"""
        # Имя файла
        self.file_name_label.setText(file_name)

        # Дефолтная подсказка alt-текста - имя файла без расширения
        stem = Path(file_name).stem
        self.alt_input.setPlaceholderText(stem)

        # Caption пустой
        self.caption_edit.clear()

        # Сброс Advanced к дефолтам
        self.wrap_checkbox.setChecked(True)
        self.pos_right.setChecked(True)
        self.type_combo.setCurrentIndex(0)
        self.border_checkbox.setChecked(False)
        self.size_default_radio.setChecked(True)

        # Дефолтные размеры из картинки
        file_path = WIKI_IMAGES_DIR / file_name
        if file_path.exists():
            pixmap = QPixmap(str(file_path))
            if not pixmap.isNull():
                self.width_spin.setValue(pixmap.width())
                self.height_spin.setValue(pixmap.height())

    # ----- Прочие утилиты -----

    def _update_buttons_for_page(self, page_index):
        """Показывает/скрывает кнопки в зависимости от страницы"""
        if page_index == 0: # Галерея
            self.back_btn.setVisible(False)
            self.use_btn.setVisible(False)
            self.insert_btn.setVisible(False)
            self.cancel_btn.setVisible(True)
        elif page_index == 1: # Предпросмотр
            self.back_btn.setVisible(True)
            self.use_btn.setVisible(True)
            self.insert_btn.setVisible(False)
            self.cancel_btn.setVisible(True)
        elif page_index == 2: # Редактор
            self.back_btn.setVisible(False)
            self.use_btn.setVisible(False)
            self.insert_btn.setVisible(True)
            self.cancel_btn.setVisible(True)

    def _on_back(self):
        """Возврат на предыдущую страницу"""
        current = self.stack.currentIndex()
        if current > 0:
            self.stack.setCurrentIndex(current - 1)
            self._update_buttons_for_page(current - 1)

    def _on_use_this_image(self):
        """Переход на страницу редактора с выбранной картинкой"""
        if not self.selected_file:
            QMessageBox.warning(self, "Ошибка", "Сначала выберите изображение")
            return
        self._update_editor(self.selected_file)
        self.stack.setCurrentIndex(2)
        self._update_buttons_for_page(2)

    def _on_insert(self):
        """Вставка изображения"""
        self.accept()

    def get_html(self):
        """Образует итоговый HTML картинки с нужными стилями"""
        if not self.selected_file:
            return ""

        src = f"WikiImages/{self.selected_file}"
        alt = self.alt_input.text().strip() or self.selected_file
        caption = self.caption_edit.toPlainText().strip()

        # --- Размер ---
        size_style = ""
        if self.size_custom_radio.isChecked():
            width = self.width_spin.value()
            height = self.height_spin.value()
            size_style = f"width: {width}px; height: {height}px;"

        # --- Позиция ---
        pos_style = ""
        if self.wrap_checkbox.isChecked():
            if self.pos_left.isChecked():
                pos_style = "float: left; margin-left: 15px; margin-right: 15px; margin-bottom: 10px;"
            elif self.pos_center.isChecked():
                pos_style = "display: block; margin: 15px auto;"
            elif self.pos_right.isChecked():
                pos_style = "float: right; margin-left: 15px; margin-right: 15px; margin-bottom: 10px;"
        else:
            pos_style = "display: inline-block; vertical-align: middle;"

        # --- Тип изображения (style для IMG) ---
        type_style = ""
        img_type = self.type_combo.currentText().lower()
        if img_type == "frameless":
            type_style = "border: none;"
        elif img_type == "frame":
            type_style = "border: 1px solid #888; padding: 4px;"
        elif img_type == "thumbnail":
            type_style = "border: 1px solid #888; padding: 4px; background-color: #2a2a2a;"

        # --- Border checkbox (добавляется к IMG) ---
        if self.border_checkbox.isChecked() and "border" not in type_style:
            type_style += " border: 1px solid #888;"

        # === Без caption: всё на img ===
        if not caption:
            img_style = f"{size_style} {pos_style} {type_style}".strip()
            style_attr = f' style="{img_style}"' if img_style else ""
            return f'<img src="{src}" alt="{alt}" draggable="false"{style_attr}>'

        # === С caption: style для IMG = size + type; style для FIGURE = pos ===
        img_style = f"{size_style} {type_style}".strip()
        img_style_attr = f' style="{img_style}"' if img_style else ""
        img_tag = f'<img src="{src}" alt="{alt}" draggable="false"{img_style_attr}>'

        figure_style = pos_style.strip()
        figure_style_attr = f' style="{figure_style}"' if figure_style else ""

        # Классы figure
        classes = "wiki-figure"
        if img_type == "thumbnail":
            classes += " thumb"

        return f'<figure class="{classes}"{figure_style_attr}>{img_tag}<figcaption>{caption}</figcaption></figure>'