# EditorPage
from PyQt6.QtCore import Qt, pyqtSignal, QTimer
from PyQt6.QtWidgets import *
from pathlib import Path
from datetime import datetime

from .Base import BasePage
from .Base import ImageLoader
from .theme_manager import ThemeManager
from .Base import draft_manager

WIKI_DIR = Path(__file__).parent / "WikiContent"

class EditorPage(BasePage):
    """Страница редактирования вики-страниц"""
    modified_state_changed = pyqtSignal(bool)
    open_in_wiki_requested = pyqtSignal(str)

    def __init__(self, theme_manager, parent=None):
        super().__init__(parent)
        self.theme_manager = theme_manager

        self.add_title("Редактор")
        self.description_label = QLabel("Редактирование локальных HTML и CSS страниц")
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

        # Эталоны (с диска)
        self.saved_html = ""
        self.saved_css = ""

        # Флаг: есть ли несохранённые изменения
        self.is_html_modified = False
        self.is_css_modified = False

        # ===== Верхняя панель кнопок (Сохранить, Открыть в Википедии) =====
        top_bar = QHBoxLayout()

        self.save_btn = QToolButton()
        self.save_btn.setObjectName("editorSaveBtn")
        self.save_btn.setText("Сохранить")
        self.save_btn.setPopupMode(QToolButton.ToolButtonPopupMode.MenuButtonPopup)
        self.save_btn.clicked.connect(self._save_all)

        save_menu = QMenu(self.save_btn)
        save_menu.addAction("Сохранить всё", self._save_all)
        save_menu.addAction("Только HTML (Структура)", self._save_html)
        save_menu.addAction("Только CSS (Стилизация)", self._save_css)
        self.save_btn.setMenu(save_menu)

        self.open_in_wiki_btn = QPushButton("Открыть в Вики")
        self.open_in_wiki_btn.setObjectName("editorOpenWikiBtn")
        self.open_in_wiki_btn.clicked.connect(self._on_open_in_wiki)

        top_bar.addWidget(self.save_btn)
        top_bar.addWidget(self.open_in_wiki_btn)
        top_bar.addStretch()

        self.layout.addLayout(top_bar)

        # ===== Основной контент: список страниц + область редактора =====
        content_layout = QHBoxLayout()
        content_layout.setContentsMargins(0, 10, 0, 0)
        content_layout.setSpacing(10)

        # Слева - список страниц
        self.pages_list = QListWidget()
        self.pages_list.setObjectName("editorPagesList")
        self.pages_list.setFixedWidth(220)

        content_layout.addWidget(self.pages_list)

        # Список готовых страниц (Временный TODO)
        self.ready_pages = {
            "HomePage": "Главная",
            "Warrior": "Воин",
            "Archer": "Лучник",
            "Wizard": "Маг",
            "Hunter": "Охотник",
            "Berserker": "Берсерк",
            "Necromancer": "Некромант",
            "CampNPC": "Лагерная Обитель",
        }
        self.current_page_id = None

        # Заполнение списка
        for page_id, display_name in self.ready_pages.items():
            item = QListWidgetItem(display_name)
            item.setData(Qt.ItemDataRole.UserRole, page_id)
            self.pages_list.addItem(item)

        self.pages_list.currentItemChanged.connect(self._on_page_selected)

        # Справа - область редактора (Source / Visual)
        self.editor_tabs = QTabWidget()
        self.editor_tabs.setObjectName("editorTabs")

        self.visual_tab = self._make_visual_tab()
        self.source_tab = self._make_source_tab()

        self.editor_tabs.addTab(self.visual_tab, "Visual Editor")
        self.editor_tabs.addTab(self.source_tab, "Source Editor")

        # Синхронизация при переключении вкладок
        self.editor_tabs.currentChanged.connect(self._on_tab_changed)

        content_layout.addWidget(self.editor_tabs, 1)

        self.layout.addLayout(content_layout, 1)

        # Подписка на смену темы
        self.theme_manager.theme_changed.connect(self._on_theme_changed)

        # --- Таймер для автосохранения черновика (делаем через debounce) ---
        self.draft_timer = QTimer()
        self.draft_timer.setSingleShot(True)
        self.draft_timer.timeout.connect(self._auto_save_draft)

    def on_image_loaded(self, pixmap):
        """Вызывается, когда картинка успешно загружена"""
        self.image_label.setPixmap(pixmap)
        self.image_label.setText("") # Убираем текст "Загрузка"
    
    def on_image_error(self):
        """Вызывается при ошибке"""
        self.image_label.setText("Ошибка загрузки")
        self.image_label.setStyleSheet("color: red;")

    def _make_source_tab(self):
        """Создаёт содержимое вкладки Source Editor"""
        widget = QWidget()
        layout = QVBoxLayout(widget)
        layout.setContentsMargins(10, 10, 10, 10)

        # --- Панель инструментов ---
        toolbar = QHBoxLayout()

        self.reset_layout_btn = QPushButton("Сбросить панели")
        self.reset_layout_btn.setToolTip("Вернуть обе панели к 50/50")
        self.reset_layout_btn.clicked.connect(self._reset_splitter)
        toolbar.addWidget(self.reset_layout_btn)

        toolbar.addStretch()

        layout.addLayout(toolbar)

        # --- Область редактора ---
        self.source_splitter = QSplitter(Qt.Orientation.Horizontal)
        self.source_splitter.setChildrenCollapsible(True)

        self.html_editor = QPlainTextEdit()
        self.html_editor.setObjectName("htmlEditor")
        self.html_editor.setMinimumWidth(0)
        self.html_editor.setPlaceholderText("HTML текущей страницы...")

        self.css_editor = QPlainTextEdit()
        self.css_editor.setObjectName("cssEditor")
        self.css_editor.setMinimumWidth(0)
        self.css_editor.setPlaceholderText("Общий CSS Вики...")

        self.source_splitter.addWidget(self.html_editor)
        self.source_splitter.addWidget(self.css_editor)
    
        layout.addWidget(self.source_splitter, 1)

        self.html_editor.textChanged.connect(self._on_html_changed)
        self.css_editor.textChanged.connect(self._on_css_changed)
        self._update_modified_indicator()
    
        return widget


    def _make_visual_tab(self):
        """Создаёт содержимое вкладки Visual Editor"""
        widget = QWidget()
        layout = QVBoxLayout(widget)
        layout.setContentsMargins(10, 10, 10, 10)

        # --- Панель инструментов ---
        self.visual_toolbar = QHBoxLayout()
        self.visual_toolbar.addStretch()
        layout.addLayout(self.visual_toolbar)

        # --- Область предпросмотра ---
        stub = QLabel("Visual Editor в разработке...")
        stub.setAlignment(Qt.AlignmentFlag.AlignCenter)
        stub.setStyleSheet("color: #888; font-size: 14px;")

        layout.addWidget(stub, 1)

        return widget

    # Синхронизация Source <-> Visual

    def _on_tab_changed(self, index):
        """Срабатывает при переключении вкладок Source/Visual"""
        if index == 0:
            # Переключились на Visual - отдаем ему текущий HTML из Source
            self._sync_source_to_visual()
        elif index == 1:
            # Наоборот
            self._sync_visual_to_source()

    def _sync_source_to_visual(self):
        """Передаёт HTML из SE в VE (TODO)"""
        pass

    def _sync_visual_to_source(self):
        """Передаёт HTML из VE в SE (TODO)"""
        pass

    # Сохранение

    def _save_all(self):
        """Сохранить всё изменённое"""
        self._save_html()
        self._save_css()

    def _save_html(self):
        """Сохранить только HTML"""
        if not self.current_page_id:
            return
        original_name = f"{self.current_page_id.lower()}.html"
        path = WIKI_DIR / original_name
        
        self._backup_file(path)

        content = self.html_editor.toPlainText()
        path.write_text(content, encoding="utf-8")

        draft_manager.delete_draft(original_name) # Удаление черновика

        self.saved_html = content
        self.is_html_modified = False
        self._update_modified_indicator()

    def _save_css(self):
        """Сохранить только CSS"""
        if not self.current_page_id:
            return
        css_file = "style-light.css" if self.theme_manager.current_theme == "light" else "style-dark.css"
        path = WIKI_DIR / css_file
        self._backup_file(path)
            
        content = self.css_editor.toPlainText()
        path.write_text(content, encoding="utf-8")

        draft_manager.delete_draft(css_file) # Удаляем черновик

        self.saved_css = content
        self.is_css_modified = False
        self._update_modified_indicator()

    # Сброс панелей
    
    def _reset_splitter(self):
        """Возвращает обе панели к равному размеру"""
        total_width = self.source_splitter.width()
        self.source_splitter.setSizes([total_width // 2, total_width // 2])

    # Загрузка HTML и CSS
    def _on_page_selected(self, current, previous):
        """Срабатывает при выборе страницы в списке"""
        if current is None:
            return

        self._force_save_drafts()

        page_id = current.data(Qt.ItemDataRole.UserRole)
        if not page_id:
            return

        self.current_page_id = page_id
        self._load_page_content(page_id)

    def _load_page_content(self, page_id):
        self._load_html_content(page_id)
        self._load_css_content()
        self._update_modified_indicator()

    def _load_html_content(self, page_id):
        """Загружает HTML указанной страницы в редактор"""
        from .Base import load_html

        original_name = f"{page_id.lower()}.html"
        display_name = self.ready_pages.get(page_id, page_id)

        # Сначала загружаем оригинал (нужен для saved_html)
        try:
            original_content = load_html(original_name)
        except Exception as e:
            original_content = f"<!-- Ошибка загрузки: {e} -->"

        # Проверяем черновик
        draft_content = self._ask_restore_draft(original_name, display_name, "HTML")

        if draft_content is not None:
            # Пользователь выбрал восстановление
            html_content = draft_content
        else:
            html_content = original_content

        self.html_editor.setPlainText(html_content)
        self.saved_html = original_content # Всегда оригинал
        self.is_html_modified = (html_content != original_content) # Сравнение с оригиналом

    def _load_css_content(self):
        """Загружает CSS текущей темы в редактор"""
        css_file = "style-light.css" if self.theme_manager.current_theme == "light" else "style-dark.css"
        display_name = "Светлая тема" if self.theme_manager.current_theme == "light" else "Тёмная тема"

        # Оригинал
        path = WIKI_DIR / css_file
        try:
            original_content = path.read_text(encoding="utf-8")
        except FileNotFoundError:
            css_content = f"/* Файл {css_file} не найден */"

        # Проверяем черновик
        draft_content = self._ask_restore_draft(css_file, display_name, "CSS")

        if draft_content is not None:
            css_content = draft_content
        else: 
            css_content = original_content

        self.css_editor.setPlainText(css_content)
        self.saved_css = original_content # Всегда оригинал
        self.is_css_modified = (css_content != original_content)

    def _update_modified_indicator(self):
        """Обновляет метки несохранённых изменений и черновиков"""
        # Метка у имени страниц в списке
        for i in range(self.pages_list.count()):
            item = self.pages_list.item(i)
            page_id = item.data(Qt.ItemDataRole.UserRole)
            display_name = self.ready_pages.get(page_id, page_id)

            # Если есть несохранённые изменения (для текущей страницы)
            has_changes = (page_id == self.current_page_id and 
                           (self.is_html_modified or self.is_css_modified))

            # Если есть черновик на диске
            original_name = f"{page_id.lower()}.html"
            has_draft = draft_manager.has_draft(original_name)

            # Формируем метку
            marks = ""
            if has_draft:
                marks += " 📝"
            if has_changes:
                marks += " *"

            item.setText(f"{display_name}{marks}")
            
        has_any = self.is_html_modified or self.is_css_modified
        self.modified_state_changed.emit(has_any)

    # Обработка изменений

    def _on_html_changed(self):
        """Срабатывает при любом изменении в HTML редакторе"""
        current = self.html_editor.toPlainText()
        self.is_html_modified = (current != self.saved_html)

        # Перезапускаем таймер автосохранения
        if self.is_html_modified:
            self.draft_timer.start(5000)
        else:
            # Пользователь вернул оригинал - удаляем черновик
            if self.current_page_id:
                original_name = f"{self.current_page_id.lower()}.html"
                draft_manager.delete_draft(original_name)

        # Обновление индикатора после всех операций
        self._update_modified_indicator()

    def _on_css_changed(self):
        """Срабатывает при любом изменении в CSS редакторе"""
        current = self.css_editor.toPlainText()
        self.is_css_modified = (current != self.saved_css)

        # Перезапускаем таймер автосохранения
        if self.is_css_modified:
            self.draft_timer.start(5000)
        else:
            # Вернули оригинал - черновик больше не нужен
            if self.current_page_id:
                css_file = "style-light.css" if self.theme_manager.current_theme == "light" else "style-dark.css"
                draft_manager.delete_draft(css_file)

        # Обновление индикатора после всех операций
        self._update_modified_indicator()

    # Бэкапы

    def _backup_file(self, file_path):
        """Создаёт резервную копию файла перед изменением"""
        src = Path(file_path)
        if not src.exists():
            return

        # Папка backups рядом с WikiContent
        backups_dir = src.parent / "backups"
        backups_dir.mkdir(exist_ok=True)

        # Имя бэкапа
        timestamp = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
        backup_name = f"{src.stem}_{timestamp}{src.suffix}"
        backup_path = backups_dir / backup_name

        # Копируем
        backup_path.write_bytes(src.read_bytes())

        # Чистим старые бэкапы до 10 последних
        pattern = f"{src.stem}_*{src.suffix}"
        existing = sorted(backups_dir.glob(pattern), key=lambda p: p.stat().st_mtime, reverse=True)
        for old in existing[10:]:
            old.unlink()

    def _on_open_in_wiki(self):
        """Открывает выбранную страницу в Вики"""
        if self.current_page_id:
            self.open_in_wiki_requested.emit(self.current_page_id)

    def _on_theme_changed(self, theme_name):
        """Меняет .CSS-файл при изменении стилизации"""
        if not self.current_page_id:
            return
        if self.is_css_modified:
            return

        css_file = "style-light.css" if theme_name == "light" else "style-dark.css"
        path = WIKI_DIR / css_file

        try:
            css_content = path.read_text(encoding="utf-8")
        except FileNotFoundError:
            css_content = f"/* Файл {css_file} не найден */"

        self.css_editor.setPlainText(css_content)
        self.saved_css = css_content
        self.is_css_modified = False
        self._update_modified_indicator()

    def _auto_save_draft(self):
        """Автосохранение черновиков HTML и CSS (debounce-таймер)"""
        if not self.current_page_id:
            return

        # Сохраняем черновик HTML, если есть изменения
        if self.is_html_modified:
            original_name = f"{self.current_page_id.lower()}.html"
            content = self.html_editor.toPlainText()
            draft_manager.save_draft(original_name, content)

        # Сохраняем черновик CSS, если есть изменения
        if self.is_css_modified:
            css_file = "style-light.css" if self.theme_manager.current_theme == "light" else "style-dark.css"
            content = self.css_editor.toPlainText()
            draft_manager.save_draft(css_file, content)

    def _force_save_drafts(self):
        """
        Принудительно сохраняет черновики (не дожидаясь debounce),
        Вызывается переключением страницы или закрытием приложения
        """
        if not self.current_page_id:
            return

        if self.is_html_modified:
            original_name = f"{self.current_page_id.lower()}.html"
            content = self.html_editor.toPlainText()
            draft_manager.save_draft(original_name, content)
    
        if self.is_css_modified:
            css_file = "style-light.css" if self.theme_manager.current_theme == "light" else "style-dark.css"
            content = self.css_editor.toPlainText()
            draft_manager.save_draft(css_file, content)

    def _ask_restore_draft(self, original_name, display_name, content_type):
        """
        Спрашивает пользователя о восстановлении черновика
        --
        original_name - имя файла ('necromancer.html')
        display_name - человеко-читаемое ('Некромант')
        content_type - 'HTML' или 'CSS' (для текста сообщения)
        --
        Возвращает: содержимое черновика (str) или None (загружать оригинал)
        """

        draft_content, saved_at = draft_manager.load_draft(original_name)
        if draft_content is None:
            return None

        # Проверка: черновик совпадает с оригиналом - удаляем
        original_path = WIKI_DIR / original_name
        if original_path.exists():
            original_content = original_path.read_text(encoding="utf-8")
            if draft_content == original_content:
                draft_manager.delete_draft(original_name)
                return None

        # Показываем диалог
        saved_at_display = datetime.fromisoformat(saved_at).strftime("%d.%m.%Y %H:%M") # Форматируем ISO в человекочитаемый
        msg = QMessageBox(self)
        msg.setWindowTitle("Найден черновик")
        msg.setIcon(QMessageBox.Icon.Question)
        msg.setText(
            f"Есть несохранённый черновик {content_type} для '{display_name}'.\n"
            f"Сохранён: {saved_at_display}"
        )
        msg.setInformativeText("Что сделать?")

        btn_restore = msg.addButton("Восстановить", QMessageBox.ButtonRole.AcceptRole)
        btn_delete = msg.addButton("Удалить", QMessageBox.ButtonRole.DestructiveRole)
        btn_original = msg.addButton("Оригинал", QMessageBox.ButtonRole.RejectRole)

        msg.exec()

        clicked = msg.clickedButton()
        if clicked == btn_restore:
            return draft_content
        elif clicked == btn_delete:
            draft_manager.delete_draft(original_name)
            return None
        else: # btn_original
            return None