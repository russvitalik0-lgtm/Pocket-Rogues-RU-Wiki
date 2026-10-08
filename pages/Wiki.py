# WikiPage
from PyQt5.QtCore import Qt, pyqtSignal, QTimer
from PyQt5.QtWidgets import *
from .Base import BasePage
from .Base import ImageLoader
from .Base import load_html
from .Base import history_manager


class WikiPage(BasePage):
    def __init__(self, parent=None):
        super().__init__(parent)

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
        pages_config = {}
        for page in self.pages_list: # Можно и через генератор словаря, но этот вариант более читаемый
            key = page.replace(' ', '')
            value = page.replace(' ', '').lower() + '.html'
            pages_config[key] = value

        # Добавление разделов
        self.menu = WikiMenu(self, pages_config)

        # Создаем метку
        self.image_label = QLabel("Загрузка...")
        self.image_label.setAlignment(Qt.AlignRight | Qt.AlignTop)

        # Верхняя панель
        Hlayout = QHBoxLayout()
        Hlayout.addWidget(self.menu, alignment=Qt.AlignLeft | Qt.AlignBottom)
        Hlayout.addWidget(self.image_label, alignment= Qt.AlignRight | Qt.AlignTop)
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
        self.add_stretch()

        # Создаем stacked widget для окна с контентом
        self.content_stack = QStackedWidget()
        self.layout.addWidget(self.content_stack, 1)

        # Создаем страницы и добавляем в стек
        self.pages = {}
        for page_id, file_name in pages_config.items():
            page = self.create_text_page(file_name)
            self.content_stack.addWidget(page)
            self.pages[page_id] = page

        self.content_stack.setCurrentWidget(self.pages["HomePage"]) # По умолчанию показываем Главную страницу

        # Подключаем сигналы от меню
        self.menu.section_changed.connect(self.change_section)

    def create_text_page(self, html_file):
        """Создает страницу из HTML файла"""
        browser = QTextBrowser()
        html_content = load_html(html_file)
        browser.setHtml(html_content)
        browser.setOpenExternalLinks(True)
        return browser

    def change_section(self, section_id):
        """Переключает контент по ID раздела"""
        if section_id in self.pages:
            self.content_stack.setCurrentWidget(self.pages[section_id])
            # Добавляем страницу в историю
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

class WikiMenu(QWidget):
    section_changed = pyqtSignal(str) # Будем переключать страницы используя их текстовой ID

    def __init__(self, parent=None, pages_config=None):
        super().__init__(parent)

        self.pages_config = pages_config or {}

        self.menubar = QMenuBar()
        self.menubar.setStyleSheet("""
                QMenuBar {
                font-size: 14px;  /* размер текста разделов */
            }
            QMenuBar::item {
                margin-right: 15px;  /* отступ справа от каждого пункта */
            }
        """)

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

        obsidiantower = location.addAction("Обсидиановая Башня")
        obsidiantower.triggered.connect(lambda: self.on_section_clicked("Obsidian Tower"))

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

        bestiary = library.addAction("Бестиарий") # Бестиарий добавляем без автоматизации, т.к. он один
        bestiary.triggered.connect(lambda: self.on_section_clicked("Bestiary"))

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