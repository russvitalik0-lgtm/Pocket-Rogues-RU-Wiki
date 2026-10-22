# EditorPage
from PyQt6.QtCore import Qt, pyqtSignal, QTimer, QUrl
from PyQt6.QtWebEngineWidgets import QWebEngineView
from PyQt6.QtGui import QColor
from PyQt6.QtWidgets import *
from pathlib import Path
from datetime import datetime
from bs4 import BeautifulSoup
import webbrowser
import os
import re

from .Base import BasePage
from .Base import ImageLoader
from .theme_manager import ThemeManager
from .Base import draft_manager
from .syntax_highlighters import HtmlHighlighter, CssHighlighter
from .link_interceptor import InterceptingPage
from .Base import load_html

from .dialogs.link_dialog import LinkDialog
from .dialogs.image_dialog import ImageDialog

WIKI_DIR = Path(__file__).parent / "WikiContent"

class EditorPage(BasePage):
    """Страница редактирования вики-страниц"""
    modified_state_changed = pyqtSignal(bool)
    open_in_wiki_requested = pyqtSignal(str)

    def __init__(self, theme_manager, parent=None):
        super().__init__(parent)
        self.theme_manager = theme_manager
        self._ui_ready = False
        self.visual_ready = False
        self.visual_page_id = None # для какой страницы уже готов VE
        self._syncing_from_visual = False # Защита от цикла при синхронизации VE в SE (Автосохранение)
        self._pending_save_after_sync = False

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

        # ===== Верхняя панель кнопок (Сохранить) =====
        top_bar = QHBoxLayout()

        self.save_btn = QToolButton()
        self.save_btn.setObjectName("editorSaveBtn")
        self.save_btn.setMaximumWidth(40)
        self.save_btn.setText("Сохранить")
        self.save_btn.setPopupMode(QToolButton.ToolButtonPopupMode.MenuButtonPopup)
        self.save_btn.clicked.connect(self._save_all)

        save_menu = QMenu(self.save_btn)
        save_menu.addAction("Сохранить всё", self._save_all)
        save_menu.addAction("Только HTML (Структура)", self._save_html)
        save_menu.addAction("Только CSS (Стилизация)", self._save_css)
        self.save_btn.setMenu(save_menu)

        top_bar.addStretch()
        top_bar.addWidget(self.save_btn)

        self.layout.addLayout(top_bar)

        # ===== Основной контент: список страниц + область редактора =====
        content_layout = QHBoxLayout()
        content_layout.setContentsMargins(0, 10, 0, 0)
        content_layout.setSpacing(10)

        # Лайаут (вспомогательный)
        left_column = QVBoxLayout()
        left_column.setContentsMargins(0, 0, 0, 0)
        left_column.setSpacing(10)

        self.open_in_wiki_btn = QPushButton("Открыть в Вики")
        self.open_in_wiki_btn.setObjectName("editorOpenWikiBtn")
        self.open_in_wiki_btn.setFixedWidth(220)
        self.open_in_wiki_btn.clicked.connect(self._on_open_in_wiki)

        # Слева - список страниц
        self.pages_list = QListWidget()
        self.pages_list.setObjectName("editorPagesList")
        self.pages_list.setFixedWidth(220)

        left_column.addWidget(self.pages_list)
        left_column.addWidget(self.open_in_wiki_btn)

        content_layout.addLayout(left_column)

        # Список готовых страниц (Временный)
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

        # Подписка на изменение страницы
        self._ui_ready = True
        self.pages_list.currentItemChanged.connect(self._on_page_selected)

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
        self.reset_layout_btn.setObjectName("reset_layout_btn")
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
        self.html_highlighter = HtmlHighlighter(self.html_editor.document())

        self.css_editor = QPlainTextEdit()
        self.css_editor.setObjectName("cssEditor")
        self.css_editor.setMinimumWidth(0)
        self.css_editor.setPlaceholderText("Общий CSS Вики...")
        self.css_highlighter = CssHighlighter(self.css_editor.document())

        self.source_splitter.addWidget(self.html_editor)
        self.source_splitter.addWidget(self.css_editor)
    
        layout.addWidget(self.source_splitter, 1)

        self.html_editor.textChanged.connect(self._on_html_changed)
        self.css_editor.textChanged.connect(self._on_css_changed)
        self._update_modified_indicator()
    
        return widget


    def _make_visual_tab(self):
        """Создаёт содержимое вкладки Visual Editor (TODO)"""
        widget = QWidget()
        layout = QVBoxLayout(widget)
        layout.setContentsMargins(10, 10, 10, 10)

        # --- Панель инструментов ---
        self.visual_toolbar = QHBoxLayout()

        # - Группа 1: отмена/повтор
        self.undo_btn = QToolButton()
        self.undo_btn.setText("↶")
        self.undo_btn.setToolTip("Отменить (Ctrl+Z)")
        self.undo_btn.clicked.connect(lambda: self._exec_js("document.execCommand('undo')"))
        self.visual_toolbar.addWidget(self.undo_btn)

        self.redo_btn = QToolButton()
        self.redo_btn.setText("↷")
        self.redo_btn.setToolTip("Повторить (Ctrl+Y)")
        self.redo_btn.clicked.connect(lambda: self._exec_js("document.execCommand('redo')"))
        self.visual_toolbar.addWidget(self.redo_btn)

        # Разделитель
        self.visual_toolbar.addSpacing(7)
        self.visual_toolbar.addWidget(QLabel('|'))
        self.visual_toolbar.addSpacing(7)

        # - Группа 2: Стиль параграфа
        self.paragraph_style = QComboBox()
        self.paragraph_style.addItems([
            "Normal",
            "Heading",
            "Sub-heading 1",
            "Sub-heading 2",
            "Sub-heading 3",
            "Sub-heading 4",
            "Preformatted",
        ])
        self.paragraph_style.setToolTip("Стиль параграфа")
        self.paragraph_style.setMinimumWidth(140)
        self.paragraph_style.currentIndexChanged.connect(self._on_paragraph_style_changed)
        self.visual_toolbar.addWidget(self.paragraph_style)

        # Разделитель
        self.visual_toolbar.addSpacing(7)
        self.visual_toolbar.addWidget(QLabel('|'))
        self.visual_toolbar.addSpacing(7)

        # - Группа 3: B, I
        self.bold_btn = QToolButton()
        self.bold_btn.setText("B")
        self.bold_btn.setStyleSheet("font-weight: bold;")
        self.bold_btn.setToolTip("Жирный (Ctrl+B)")
        self.bold_btn.clicked.connect(lambda: self._exec_js("document.execCommand('bold')"))
        self.visual_toolbar.addWidget(self.bold_btn)

        self.italic_btn = QToolButton()
        self.italic_btn.setText("I")
        self.italic_btn.setStyleSheet("font-style: italic;")
        self.italic_btn.setToolTip("Курсив (Ctrl+I)")
        self.italic_btn.clicked.connect(lambda: self._exec_js("document.execCommand('italic')"))
        self.visual_toolbar.addWidget(self.italic_btn)

        self.decorations_btn = QToolButton()
        self.decorations_btn.setText("T")
        self.decorations_btn.setToolTip("Текстовые декорации")
        self.decorations_btn.setPopupMode(QToolButton.ToolButtonPopupMode.InstantPopup)

        decorations_menu = QMenu(self.decorations_btn)
        decorations_menu.addAction("Underline", lambda: self._exec_js("document.execCommand('underline')"))
        decorations_menu.addAction("Strikethrough", lambda: self._exec_js("document.execCommand('strikeThrough')"))
        decorations_menu.addAction("Superscript", lambda: self._exec_js("document.execCommand('superscript')"))
        decorations_menu.addAction("Subscript", lambda: self._exec_js("document.execCommand('subscript')"))
        decorations_menu.addAction("Clear formatting", lambda: self._exec_js("document.execCommand('removeFormat')"))

        self.decorations_btn.setMenu(decorations_menu)
        self.visual_toolbar.addWidget(self.decorations_btn)

        # Разделитель
        self.visual_toolbar.addSpacing(7)
        self.visual_toolbar.addWidget(QLabel('|'))
        self.visual_toolbar.addSpacing(7)

        # - Группа 4: списки и Indent
        self.ul_btn = QToolButton()
        self.ul_btn.setText("• ≡")
        self.ul_btn.setToolTip("Пунктированный список")
        self.ul_btn.clicked.connect(lambda: self._exec_js("document.execCommand('insertUnorderedList')"))
        self.visual_toolbar.addWidget(self.ul_btn)

        self.ol_btn = QToolButton()
        self.ol_btn.setText("1. ≡")
        self.ol_btn.setToolTip("Нумерованный список")
        self.ol_btn.clicked.connect(lambda: self._exec_js("document.execCommand('insertOrderedList')"))
        self.visual_toolbar.addWidget(self.ol_btn)

        self.list_indent = QToolButton()
        self.list_indent.setText(">≡")
        self.list_indent.setToolTip("Структура")
        self.list_indent.setPopupMode(QToolButton.ToolButtonPopupMode.InstantPopup)

        indentation_menu = QMenu(self.list_indent)
        indentation_menu.addAction("Increase indentation", lambda: self._exec_js("document.execCommand('indent')"))
        indentation_menu.addAction("Decrease indentation", lambda: self._exec_js("document.execCommand('outdent')"))

        self.list_indent.setMenu(indentation_menu)
        self.visual_toolbar.addWidget(self.list_indent)

        # Разделитель
        self.visual_toolbar.addSpacing(7)
        self.visual_toolbar.addWidget(QLabel('|'))
        self.visual_toolbar.addSpacing(7)

        # - Группа 5: Вставка
        self.link_btn = QToolButton()
        self.link_btn.setText("🔗")
        self.link_btn.setToolTip("Гиперссылка")
        self.link_btn.clicked.connect(self._on_link_btn_clicked)
        self.visual_toolbar.addWidget(self.link_btn)

        self.image_btn = QToolButton()
        self.image_btn.setText("")
        self.image_btn.setToolTip("Вставка изображения")
        self.image_btn.clicked.connect(self._on_image_btn_clicked)
        self.visual_toolbar.addWidget(self.image_btn)

        self.insert_btn = QToolButton()
        self.insert_btn.setText("INSERT")
        self.insert_btn.setToolTip("Вставить элемент")
        self.insert_btn.setPopupMode(QToolButton.ToolButtonPopupMode.InstantPopup)
        self._build_insert_menu()
        self.visual_toolbar.addWidget(self.insert_btn)

        # Отступ
        self.visual_toolbar.addStretch()

        layout.addLayout(self.visual_toolbar)

        # --- Область предпросмотра ---
        self.visual_view = QWebEngineView()
        self.visual_page = InterceptingPage(self.visual_view)
        self.visual_page.on_external_link = lambda url: webbrowser.open(url.toString())
        self.visual_view.setPage(self.visual_page)
        self.visual_page.on_visual_changed = self._on_visual_changed
        self._apply_visual_background()

        # Подписка на загрузку и изменения страницы
        self.visual_view.loadFinished.connect(self._on_visual_loaded)

        layout.addWidget(self.visual_view, 1)

        return widget

    def _apply_visual_background(self):
        """Устанавливает фон QWebEngineView под текущую тему"""
        theme = self.theme_manager.current_theme
        if theme == "light":
            color = QColor("#f0f0f0")
        else:
            color = QColor("#2a2a2a")
        self.visual_page.setBackgroundColor(color)

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
        """Передаёт HTML из SE в VE"""
        if not self.current_page_id:
            return

        html_content = self.html_editor.toPlainText()
        css_content = self.css_editor.toPlainText()

        soup = BeautifulSoup(html_content, "html.parser")

        # Заменяем <link rel="stylesheet"> на <style> с CSS из редактора
        for link in soup.find_all("link", rel="stylesheet"):
            style = soup.new_tag("style")
            style.string = css_content
            link.replace_with(style)

        # Находим body, оборачиваем содержимое в редактируемый div
        body = soup.body
        if body:
            wrapper = soup.new_tag("div", id="editor-content")
            wrapper["contenteditable"] = "true"
            for child in list(body.children):
                wrapper.append(child.extract())
            body.append(wrapper)

        # Проверка ДО этого принта не должна стоять. Проверка ПОСЛЕ:
        check = soup.find("div", id="editor-content")

        # Инжектим CSS для рамок блочных элементов в head
        head = soup.head 
        if head:
            editor_css = soup.new_tag("style")
            editor_css.string = """
            #editor-content {
                outline: none !important;
            }
            #editor-content:focus {
                outline: none !important;
            }
            .wiki-table, .wiki-quote, .wiki-infobox,
            .wiki-collapsible, .wiki-figure {
                outline: 1px dashed rgba(0, 183, 224, 0.35) !important;
                outline-offset: 2px !important;
            }
            .wiki-table:hover, .wiki-quote:hover, .wiki-infobox:hover,
            .wiki-collapsible:hover, .wiki-figure:hover {
                outline-color: rgba(0, 183, 224, 0.85) !important;
            }
            """
            head.append(editor_css)

        base_url = QUrl.fromLocalFile(str(WIKI_DIR) + os.sep)
        html_str = str(soup)
        self.visual_ready = False
        self.visual_view.setHtml(html_str, base_url)
        self.visual_page_id = self.current_page_id

    def _sync_visual_to_source(self):
        """Передаёт HTML из VE в SE"""
        if not self.current_page_id:
            return
        if not self.visual_ready:
            return
        if self.visual_page_id != self.current_page_id:
            return

        js_code = """
        (function() {
            var el = document.getElementById('editor-content');
            console.log('__JS_HAS_EL__', el !== null);
            return el ? el.innerHTML : '';
        })();
        """
        self.visual_view.page().runJavaScript(js_code, self._on_visual_html_received)

    def _on_visual_html_received(self, inner_html):
        """Callback от Visual: получаем innerHTML и обновляем html_editor"""
        if not inner_html or not inner_html.strip():
            return

        html_content = self.html_editor.toPlainText()
        soup = BeautifulSoup(html_content, "html.parser")
        body = soup.body
        if not body:
            return

        for child in list(body.children):
            child.extract()

        new_content = BeautifulSoup(inner_html, "html.parser")
        source = new_content.body if new_content.body else new_content
        for child in list(source.children):
            body.append(child)

        full_html = str(soup)

        # Обновляем html_editor с флагом - чтобы не циклить
        self._syncing_from_visual = True
        self.html_editor.setPlainText(full_html)
        self._syncing_from_visual = False

        # Сравниваем, нормализуя оригинал через тот же парсер
        normalized_saved = str(BeautifulSoup(self.saved_html, "html.parser"))

        if full_html == normalized_saved:
            # Изменений нет
            self.is_html_modified = False
            if self.current_page_id:
                original_name = f"{self.current_page_id.lower()}.html"
                draft_manager.delete_draft(original_name)
        else:
            self.is_html_modified = True
            if self.current_page_id:
                original_name = f"{self.current_page_id.lower()}.html"
                draft_manager.save_draft(original_name, full_html)

        self._update_modified_indicator()

    # Сохранение

    def _save_all(self):
        """Сохранить всё изменённое"""
        self._save_html()
        self._save_css()

    def _save_html(self):
        """Сохранить только HTML"""
        if not self.current_page_id:
            return

        # Если открыт VE и есть несохранённые изменения - сначала синхронизируем:
        if self.editor_tabs.currentIndex() == 0 and self.visual_ready:
            # Синхронизация ассинхронна, но ждать придется. Проще: чтение innerHTML, однако runJavaScript тоже асинхронный. Просто вызовем функцию синхронизации и сохраним в callback
            self._pending_save_after_sync = True # флаг
            self._sync_visual_to_source()
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

    def _on_visual_loaded(self, ok):
        """Срабатывает при загрузке страницы в VISUAL EDITOR"""
        if not ok:
            self.visual_ready = False
            return
        self.visual_ready = True

        # Отслеживаем изменения в VE
        js = """
        (function() {
            var el = document.getElementById('editor-content');
            if (!el) {
                console.log('__VISUAL_TRACKER_NO_EL__');
                return;
            }
            el.addEventListener('input', function() {
                console.log('__VISUAL_CHANGED__');
            });
            console.log('__VISUAL_TRACKER_INSTALLED__');
        })();
        """
        self.visual_view.page().runJavaScript(js)

    def _on_visual_changed(self):
        """Пользователь внес изменения в VE - перезапускаем debounce"""
        if self.current_page_id:
            self.draft_timer.start(5000)

    # Сброс панелей
    
    def _reset_splitter(self):
        """Возвращает обе панели к равному размеру"""
        total_width = self.source_splitter.width()
        self.source_splitter.setSizes([total_width // 2, total_width // 2])

    # Загрузка HTML и CSS
    def _on_page_selected(self, current, previous):
        """Срабатывает при выборе страницы в списке"""
        if not self._ui_ready:
            return
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

        self.visual_ready = False
        self.visual_page_id = None

        if self.editor_tabs.currentIndex() == 0:
            self._sync_source_to_visual()

    def _load_html_content(self, page_id):
        """Загружает HTML указанной страницы в редактор"""
        from .Base import load_html

        original_name = f"{page_id.lower()}.html"
        display_name = self.ready_pages.get(page_id, page_id)

        # Сначала загружаем оригинал (нужен для saved_html)
        path = WIKI_DIR / f"{page_id.lower()}.html"
        try:
            original_content = path.read_text(encoding="utf-8")
        except FileNotFoundError:
            original_content = f"<!-- Файл {page_id.lower()}.html не найден -->"

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
            original_content = f"/* Файл {css_file} не найден */"

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
        if self._syncing_from_visual: # Избавляемся от цикла
            return

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

        self._apply_visual_background() # Обновление фона QWebEngineView

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
        if not self.current_page_id:
            return

        # Если открыт VE - сохраняем напрямую
        if self.editor_tabs.currentIndex() == 0 and self.visual_ready:
            self._save_visual_draft_async()
            return

        # Для SE:

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

        # Открыт VE - сохраняем напрямую из VE
        if self.editor_tabs.currentIndex() == 0 and self.visual_ready:
            self._save_visual_draft_async()
            return

        # SE сохраняем напрямую
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

    def _save_visual_draft_async(self):
        """Асинхронно сохраняет черновик из VE (для тек. страницы)"""
        if not self.current_page_id or not self.visual_ready or self.visual_page_id != self.current_page_id:
            return

        # Запоминаем страницу
        page_id = self.current_page_id

        js_code = """
        (function() {
            var el = document.getElementById('editor-content');
            return el ? el.innerHTML : '';
        })();
        """
        self.visual_view.page().runJavaScript(
            js_code,
            lambda html: self._on_visual_draft_received(html, page_id)
        )

    def _on_visual_draft_received(self, inner_html, page_id):
        """Callback: получает innerHTML и сохраняет черновик для указанной страницы"""
        if not inner_html or not inner_html.strip():
            return

        # Собираем полный HTML
        original_path = WIKI_DIR / f"{page_id.lower()}.html"
        try:
            original_content = original_path.read_text(encoding="utf-8")
        except FileNotFoundError:
            return

        soup = BeautifulSoup(original_content, "html.parser")
        body = soup.body
        if not body:
            return

        for child in list(body.children):
            child.extract()

        new_content = BeautifulSoup(inner_html, "html.parser")
        source = new_content.body if new_content.body else new_content
        for child in list(source.children):
            body.append(child)

        full_html = str(soup)

        normalized_saved = str(BeautifulSoup(original_content, "html.parser"))

        # Сохраняем только если отличается
        if full_html != normalized_saved:
            draft_manager.save_draft(f"{page_id.lower()}.html", full_html)
        else: # Удаляем
            draft_manager.delete_draft(f"{page_id.lower()}.html")
    

    # --- VISUAL EDITOR: Панель инструментов ---
    def _exec_js(self, js):
        """Выполняет JS в VE"""
        if not self.visual_ready:
            return
        self.visual_view.page().runJavaScript(js)

    def _js_escape(self, html):
        """Экранирует HTML для вставки в JS-строку"""
        return html.replace("\\", "\\\\").replace("'", "\\'").replace("\n", "\\n")

    def _insert_html(self, html):
        """Вставляет HTML в позицию курсора в VE с новой строки"""
        escaped = self._js_escape(html)
        js = f"document.execCommand('insertHTML', false, '<br>{escaped}<br>')"
        self._exec_js(js)

    def _insert_html_inline(self, html):
        """Вставляет HTML в позицию курсора в VE"""
        escaped = self._js_escape(html)
        js = f"document.execCommand('insertHTML', false, '{escaped}')"
        self._exec_js(js)

    def _on_paragraph_style_changed(self, index):
        """Смена стиля параграфа через execCommand formatBlock"""
        # Соответствие - индекс -> HTML-тег
        tag_map = {
            0: "p",
            1: "h1",
            2: "h2",
            3: "h3",
            4: "h4",
            5: "h5",
            6: "pre",
        }
        tag = tag_map.get(index)
        if not tag:
            return
        self._exec_js(f"document.execCommand('formatBlock', false, '<{tag}>')")

    # Гиперссылка
    def _on_link_btn_clicked(self):
        """Получаем выделенный текст из VE"""
        self.visual_view.page().runJavaScript(
            "window.getSelection().toString()",
            self._on_link_selection_received
        )

    def _on_link_selection_received(self, selected_text):
        """Получаем заголовки"""
        js = """
        (function() {
            var headers = document.querySelectorAll('#editor-content h1[id], #editor-content h2[id], #editor-content h3[id], #editor-content h4[id]');
            return Array.from(headers).map(function(h) {
                return {id: h.id, text: h.textContent.trim()};
            });
        })();
        """
        self.visual_view.page().runJavaScript(
            js,
            lambda headers: self._open_link_dialog(selected_text, headers)
        )

    def _open_link_dialog(self, selected_text, headers):
        """Открывает диалог с переданным списком заголовков"""
        dialog = LinkDialog( # Предзаполнение если есть выделенный фрагмент текста
            self,
            selected_text=selected_text or "",
            anchors=headers or []
            )
        if dialog.exec() == QDialog.DialogCode.Accepted:
            url = dialog.get_url()
            if url == "None":
                self._exec_js("document.execCommand('unlink')")
            else:
                text = dialog.get_text()
                # Вставляем ссылку
                link_html = f'<a href="{url}">{text}</a>'
                self._insert_html_inline(link_html)

    def _on_image_btn_clicked(self):
        """TODO"""
        dialog = ImageDialog(self)
        if dialog.exec() == QDialog.DialogCode.Accepted:
            html = dialog.get_html()
            if html:
                self._insert_html(html)

    def _build_insert_menu(self):
        """Строит меню INSERT с элементами вставки"""
        menu = QMenu(self.insert_btn)

        # Заглушки (TODO)
        menu.addAction("Table", lambda: self._not_implemented("Table"))
        menu.addAction("Infobox", self._insert_infobox_template)
        menu.addAction("Structured Quote", self._insert_quote_template)
        menu.addAction("Comment", self._insert_comment)
        menu.addAction("Code block", self._insert_code_block)
        menu.addAction("Galerry", lambda: self._not_implemented("Gallery"))
        menu.addAction("Math formula", lambda: self._not_implemented("Math formula"))

        menu.addSeparator()

        # Подменю Templates
        templates_menu = menu.addMenu("Templates")
        templates_menu.addAction("Notes", self._insert_wiki_notes)
        templates_menu.addAction("Collapsible block", self._insert_collapsible)
        templates_menu.addAction("Perks table", self._insert_perks_table)

        self.insert_btn.setMenu(menu)

    def _not_implemented(self, name):
        """Заглушка для нереализованных пунктов"""
        pass

    # Заготовки шаблонов
    def _insert_infobox_template(self):
        html = '''<aside class="wiki-infobox">
    <div class="wiki-infobox__title">Заголовок</div>
    <div class="wiki-infobox__image"><img draggable="false" src="WikiImages/placeholder.png" alt=""></div>
    <div class="wiki-infobox__caption">Подпись</div>
    <div class="wiki-infobox__header">Характеристики</div>
    <dl class="wiki-infobox__fields">
    <div class="wiki-infobox__row"><dt>Поле:</dt><dd>Значение</dd></div>
    <div class="wiki-infobox__row"><dt>Поле:</dt><dd>Значение</dd></div>
    </dl>
    </aside>'''
        self._insert_html(html)


    def _insert_quote_template(self):
        html = '''<blockquote class="wiki-quote">
    <p>Текст цитаты.</p>
    <footer class="wiki-quote-attr">— Автор</footer>
    </blockquote>'''
        self._insert_html(html)


    def _insert_comment(self):
        self._insert_html("<!-- комментарий -->")


    def _insert_code_block(self):
        self._insert_html("<pre><code>код</code></pre>")

    def _insert_wiki_notes(self):
        html = '''<div class="wiki-notes">
    <strong>Примечания:</strong>
    <ul>
    <li>Первый пункт</li>
    <li>Второй пункт</li>
    </ul>
    </div>'''
        self._insert_html(html)


    def _insert_collapsible(self):
        html = '''<details class="wiki-collapsible">
    <summary>Заголовок</summary>
    <div class="wiki-collapsible-content">
    <p>Содержимое</p>
    </div>
    </details>'''
        self._insert_html(html)


    def _insert_perks_table(self):
        html = '''<table class="wiki-table">
    <thead>
    <tr><th>Название</th><th>Описание</th></tr>
    </thead>
    <tbody>
    <tr><td>Перк 1</td><td>Описание</td></tr>
    <tr><td>Перк 2</td><td>Описание</td></tr>
    </tbody>
    </table>'''
        self._insert_html(html)