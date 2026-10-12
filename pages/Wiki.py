# WikiPage
from PyQt6.QtCore import Qt, pyqtSignal, QTimer, QUrl
from PyQt6.QtWidgets import *
from PyQt6.QtWebEngineWidgets import QWebEngineView
from PyQt6.QtGui import QColor
import os
import webbrowser

from .Base import BasePage
from .Base import ImageLoader
from .Base import load_html
from .Base import history_manager
from .Base import saved_manager
from .link_interceptor import InterceptingPage


class WikiPage(BasePage):
    fullscreen_requested = pyqtSignal()
    save_toggle_requested = pyqtSignal()

    def __init__(self, theme_manager, parent=None):
        super().__init__(parent)
        self.theme_manager = theme_manager

        # Используем переданный менеджер
        self.history_manager = history_manager

        self.add_title("Pocket Rogues RU-Wiki")

        # Автоматическое создание словаря для страниц с использованием списка в виде хранилища
        self.pages_list = [ # Правильная последовательность страниц действительно важна | Пробелы допустимы, но прочие символы - нет.
            "HomePage",
            "Warrior",
            "Archer",
            "Wizard",
            "Hunter",
            "Berserker",
            "Necromancer",
            "CampNPC",
            "UndergroundNPC",
            "Weapons",
            "Armor",
            "Hat",
            "Second Hand",
            "Rings",
            "Artefacts",
            "Usable Items",
            "Other Items",
            "Passive Items",
            "Materials",
            "Effects",
            "Fortress",
            "Smithy",
            "Shop",
            "Characteristics",
            "Containers And Chests",
            "Interactive Objects",
            "Traps",
            "Game History",
            "In Game Hints",
            "Game Versions",
            "Help",
            "Tactics",
            "Builds",
            "Bestiary",
            "Catacombs",
            "Abandoned Prison",
            "Adamantite Garden",
            "Borderlands",
            "Crypt of Emptiness",
            "Burial Mound",
            "Sunken Grotto",
            "Prologue",
            "Camp",
            "The Treasury",
            "Ambush",
            "Abandoned Crypt",
            "Rat Hole",
            "Predatory Lair",
            "Secret Sanctuary",
            "Goblin Larder",
            "Obsidian Tower"
        ]
        self.pages_config = {}
        for page in self.pages_list: # Можно и через генератор словаря, но этот вариант более читаемый
            key = page.replace(' ', '')
            value = page.replace(' ', '').lower() + '.html'
            self.pages_config[key] = value

        saved_manager.saved_changed.connect(self._on_saved_changed)

        # Добавление разделов
        self.menu = WikiMenu(self, self.pages_config)

        # Создаем метку
        self.image_label = QLabel("Загрузка...")
        self.image_label.setObjectName("pageLogo")
        self.image_label.setAlignment(Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignTop)

        # Контейнер шапки
        self.header_widget = QWidget()
        self.header_widget.setObjectName("wikiHeader")
        header_layout = QVBoxLayout(self.header_widget)
        header_layout.setContentsMargins(0, 0, 0, 0)
        header_layout.setSpacing(0)

        # Верхняя панель
        Hlayout = QHBoxLayout()
        Hlayout.addWidget(self.menu, alignment=Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignBottom)
        Hlayout.addWidget(self.image_label, alignment= Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignTop)
        Hlayout.setContentsMargins(0,0,0,0)

        # Крепим к основному лайауту
        header_layout.addLayout(Hlayout)

        self.layout.addWidget(self.header_widget)

        # Запуск загрузки картинки в отедльном потоке
        self.loader = ImageLoader()
        self.loader.finished.connect(self.on_image_loaded)
        self.loader.error.connect(self.on_image_error)
        self.loader.start()

        # Обертка
        self.browser_frame = QFrame()
        self.browser_frame.setObjectName("wikiBrowserFrame")
        browser_layout = QVBoxLayout(self.browser_frame)

        # Окно с контентом
        self.browser = QWebEngineView()
        self.browser_page = InterceptingPage(self.browser)
        self.browser_page.on_fullscreen_toggle = self.fullscreen_requested.emit
        self.browser_page.on_save_toggle = self.save_toggle_requested.emit
        self.browser_page.on_external_link = lambda url: webbrowser.open(url.toString())
        self.browser.setPage(self.browser_page)
        self.browser.loadFinished.connect(self._on_page_loaded)
        self.theme_manager.theme_changed.connect(self.apply_page_theme)

        # Обертывание
        browser_layout.setContentsMargins(1, 1, 1, 1)   # ← 1px зазор между границей и браузером
        browser_layout.setSpacing(0)
        browser_layout.addWidget(self.browser)

        self.layout.addWidget(self.browser_frame, 1)


        self.PAGE_ACTIONS_BTN = (
            '<div class="page-actions">'
                '<button class="action-btn fullscreen-btn" '
                'onclick="console.log(\'__FULLSCREEN_TOGGLE__\')">'
                    '<img draggable="false" src="WikiImages/fullscreen_icon_enter.png" class="icon-enter" alt="">'
                    '<img draggable="false" src="WikiImages/fullscreen_icon_exit.png" class="icon-exit" alt="">'
                '</button>'
                '<button class="action-btn save-btn" '
                'onclick="console.log(\'__SAVE_TOGGLE__\')">'
                    '<img draggable="false" src="WikiImages/save_icon.png" class="icon-save" alt="">'
                    '<img draggable="false" src="WikiImages/saved_icon.png" class="icon-saved" alt="">'
                '</button>'
            '</div>'
        )

        self.current_page_id = None
        self.load_page("HomePage")

        # Подключаем сигналы от меню
        self.menu.section_changed.connect(self.change_section)

    def load_page(self, page_id):
        """Загружает HTML-файл в браузер"""
        if page_id in self.pages_config:
            self.current_page_id = page_id
            file_name = self.pages_config[page_id]
            html_content = load_html(file_name)

            html_content = inject_page_actions(html_content, self.PAGE_ACTIONS_BTN)

            current_dir = os.path.dirname(os.path.abspath(__file__))
            base_path = os.path.join(current_dir, "WikiContent")
            base_url = QUrl.fromLocalFile(base_path + os.sep)

            theme_css = "style-light.css" if self.theme_manager.current_theme == "light" else "style-dark.css"
            html_content = html_content.replace('href="style.css"', f'href="{theme_css}"')

            self.browser.setHtml(html_content, base_url)

    def change_section(self, section_id):
        """Переключает контент по ID раздела"""
        if section_id in self.pages_config:
            self.load_page(section_id)
            self.history_manager.add_page(section_id)

    def on_image_loaded(self, pixmap):
        """Вызывается, когда картинка успешно загружена"""
        self.image_label.setPixmap(pixmap)
        self.image_label.setText("") # Убираем текст "Загрузка"

    def on_image_error(self):
        """Вызывается при ошибке"""
        self.image_label.setText("Ошибка загрузки")
        self.image_label.setStyleSheet("color: red;")

    def send_pages_count(self):
        """Отправляет кол-во существующих страниц"""
        pages_count = len(self.pages_list)
        return pages_count

    def set_reading_mode(self, on):
        """Скрывает/показывает шапку"""
        if on:
            self.header_widget.hide()
        else:
            self.header_widget.show()

        action = "add" if on else "remove"
        self.browser.page().runJavaScript(
            f"document.body.classList.{action}('is-fullscreen')"
        )

    def _update_save_icon(self):
        """Обновляет is-saved на <body> в соответствии с состоянием saved_manager"""
        if not self.current_page_id:
            return
        if saved_manager.is_saved(self.current_page_id):
            js = "document.body.classList.add('is-saved')"
        else:
            js = "document.body.classList.remove('is-saved')"
        self.browser_page.runJavaScript(js)

    def _on_page_loaded(self, ok):
        """Восстанавливает классы is-saved и is-fullscreen после загрузки страницы"""
        if not ok:
            return

        # Фуллскрин
        if ok and self.header_widget.isHidden():
            self.browser.page().runJavaScript(
                "document.body.classList.add('is-fullscreen')"
            )

        # Сохранение
        if self.current_page_id and saved_manager.is_saved(self.current_page_id):
            self.browser.page().runJavaScript(
                "document.body.classList.add('is-saved')"
            )

    def _on_saved_changed(self):
        """Вызывается, когда saved_manager сообщает об изменении списка сохранённых"""
        self._update_save_icon()

    def apply_page_theme(self, theme_name):
        """Перезагружает текущую страницу для применения новой темы CSS"""
        if self.current_page_id:
            self.load_page(self.current_page_id)

class WikiMenu(QWidget):
    section_changed = pyqtSignal(str) # Будем переключать страницы используя их текстовой ID

    def __init__(self, parent=None, pages_config=None):
        super().__init__(parent)
        self.setObjectName("wikiMenu")

        self.READY_PAGES = {
            "HomePage",
            "Warrior",
            "Archer",
            "Berserker",
            "Necromancer",
            "Hunter",
            "Wizard",
            "CampNPC"
        }

        self.pages_config = pages_config or {}

        self.menubar = QMenuBar()
        self.menubar.setObjectName("mainMenuBar")

        layout = QVBoxLayout(self)
        layout.addWidget(self.menubar)

        # Главная Страница
        main_action = self.menubar.addAction("HomePage")
        main_action.triggered.connect(lambda: self.section_changed.emit("HomePage"))

        # Вкладка "Персонажи" --- Изменено: Создаем методы автоматизации вместо кучи повторяющихся строк
        characters = self.add_menu_with_arrow("Персонажи")
        self.add_actions_to_menu(characters, [
            ("Warrior", "Воин"),
            ("Archer", "Лучник"),
            ("Wizard", "Маг"),
            ("Hunter", "Охотник"),
            ("Berserker", "Берсерк"),
            ("Necromancer", "Некромант")
        ])
        # Подменю "Неигровые персонажи"
        notgamechars = characters.addMenu("Неигровые персонажи")
        self.add_actions_to_menu(notgamechars, [
            ("Camp NPC", "Лагерная Обитель"),
            ("Underground NPC", "Подземелье")
        ])

        # Вкладка "Предметы"
        items = self.add_menu_with_arrow("Предметы")
        equipment = items.addMenu("Экипировка")

        self.add_actions_to_menu(items, [
            ("Usable Items", "Используемые"),
            ("Passive Items", "Пассивные предметы"),
            ("Effects", "Эффекты")
        ])
        # Подменю "Экипировка"
        self.add_actions_to_menu(equipment, [
            ("Weapons", "Оружие"),
            ("Armor", "Доспехи"),
            ("Hat", "Головные уборы"),
            ("Second Hand", "Вторая рука"),
            ("Rings", "Кольца"),
            ("Artefacts", "Артефакты")
        ])

        # "Локации"
        location = self.add_menu_with_arrow("Локации")

        # Подменю "Кампания"
        campany = location.addMenu("Кампания")
        self.add_actions_to_menu(campany, [
            ("Catacombs", "Катакомбы"),
            ("Abandoned Prison", "Заброшенная Темница"),
            ("Adamantite Garden", "Адамантитовый Сад"),
            ("Borderlands", "Пограничье")
        ])

        # Подменю "Бесконечные"
        endless = location.addMenu("Бесконечные")
        self.add_actions_to_menu(endless, [
            ("Crypt of Emptiness", "Крипта Пустоты"),
            ("Burial Mound", "Могильный Холм"),
            ("Sunken Grotto", "Затонувший Грот")
        ])

        # Подменю "Подлокации"
        specials = location.addMenu("Особые")
        self.add_actions_to_menu(specials, [
            ("Prologue", "Обучение"),
            ("Camp", "Лагерь"),
            ("The Treasury", "Сокровищница"),
            ("Ambush", "Засада"),
            ("Abandoned Crypt", "Покинутый склеп"),
            ("Rat Hole", "Крысиная нора"),
            ("Predatory Lair", "Хищное Логово"),
            ("Secret Sanctuary", "Тайное Святилище"),
            ("Goblin Larder", "Кладовая Гоблинов")

        ])

        self.add_single_action(location, "Obsidian Tower", "Обсидиановая Башня") # Автоматизируем одиночное добавление

        # "Библиотека"
        library = self.add_menu_with_arrow("Библиотека")

        # Подменю "Прогрессия"
        progression = library.addMenu("Прогрессия")
        self.add_actions_to_menu(progression, [
            ("Fortress", "Крепость"),
            ("Smithy", "Кузня"),
            ("Shop", "Магазин"),
            ("Characteristics", "Характеристики"),
        ])

        # Подменю "Объекты"
        objects = library.addMenu("Объекты")
        self.add_actions_to_menu(objects, [
            ("Containers And Chests", "Контейнеры и сундуки"),
            ("Interactive Objects", "Интерактивные объекты"),
            ("Traps", "Ловушки")
        ])

        # Подменю "Разное"
        something = library.addMenu("Разное")
        self.add_actions_to_menu(something, [
            ("Game History", "Игровой лор"),
            ("In Game Hints", "Внутриигровые подсказки"),
            ("Game Versions", "Версии игры")
        ])

        # Подменю "Помощь"
        support = library.addMenu("Помощь")
        self.add_actions_to_menu(support, [
            ("Help", "Помощь новичкам"),
            ("Tactics", "Тактики"),
            ("Builds", "Билды")
        ])

        self.add_single_action(library, "Bestiary", "Бестиарий") # Автоматизируем одиночное добавление

    # Функции для дизайна
    def add_menu_with_arrow(self, title):
        """Создает меню с автоматической сменой стрелки"""
        menu = self.menubar.addMenu(f"{title} ▼")
        menu.aboutToShow.connect(lambda: self.on_menu_show(menu))
        menu.aboutToHide.connect(lambda: self.on_menu_hide(menu))
        return menu

    def on_menu_show(self, menu):
        """Меню открывается - меняем стрелку вверх"""
        title = menu.title().replace(" ▼", "").replace(" ▲", "")
        menu.setTitle(f"{title} ▲")

    def on_menu_hide(self, menu):
        """Меню закрывается - проверяем через интервал"""
        QTimer.singleShot(200, lambda: self.update_arrow_if_hidden(menu))

    def update_arrow_if_hidden(self, menu):
        """Меняем стрелку вниз только если меню действительно скрыто"""
        if not menu.isVisible():
            title = menu.title().replace(" ▼", "").replace(" ▲", "")
            menu.setTitle(f"{title} ▼")

    # А теперь для функционала
    def on_section_clicked(self, section_id):
        id = str(section_id).replace(' ', '')
        self.section_changed.emit(id)

    def add_actions_to_menu(self, menu, actions_list):
        """Добавляет действия в меню из списка (ID, название)"""
        for page_id, title in actions_list:
            action = menu.addAction(title)
            action.triggered.connect(
                lambda checked, pid=page_id: self.on_section_clicked(pid)
            )
            if page_id.replace(' ', '') not in self.READY_PAGES:
                action.setEnabled(False)

    def add_single_action(self, menu_or_menubar, page_id, title):
        """Добавляет одиночный пункт меню с проверкой READY_PAGES"""
        action = menu_or_menubar.addAction(title)
        action.triggered.connect(
            lambda checked, pid=page_id: self.on_section_clicked(pid)
        )
        if page_id.replace(' ', '') not in self.READY_PAGES:
            action.setEnabled(False)
        return action

def inject_page_actions(html, actions_html):
    """Вставляет контейнер кнопок сразу после открывающего тега <body ...>"""
    idx_body = html.find("<body")
    if idx_body == -1:
        return html # На случай, если body нет
    idx_end = html.find(">", idx_body)
    if idx_end == -1:
        return html
    return html[:idx_end + 1] + actions_html + html[idx_end +1:]