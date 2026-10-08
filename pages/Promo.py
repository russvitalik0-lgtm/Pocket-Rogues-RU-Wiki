# PromoPage
from PyQt5.QtCore import Qt, pyqtSignal
from PyQt5.QtWidgets import *
from .Base import BasePage
from .Base import ImageLoader
from .addons_manager import AddonsManager

class PromoPage(BasePage):
    addon_activated = pyqtSignal(str, bool)

    def __init__(self, parent=None):
        super().__init__(parent)

        # Заголовок
        self.add_title("Дополнения и аддоны")

        # Создаем менеджер дополнений
        self.addons_manager = AddonsManager()

        # Создаем метку
        self.image_label = QLabel("Загрузка...")
        self.image_label.setAlignment(Qt.AlignRight | Qt.AlignTop)

        # Запуск загрузки картинки в отедльном потоке
        self.loader = ImageLoader()
        self.loader.finished.connect(self.on_image_loaded)
        self.loader.error.connect(self.on_image_error)
        self.loader.start()

        self.layout.addWidget(self.image_label)
        grid = QGridLayout()
        grid.setContentsMargins(20, 20, 20, 20)
        grid.setSpacing(15)

        self.add_separator()
    
        # Поле для ввода
        self.code_input = QLineEdit()
        self.code_input.setPlaceholderText("Введите код...")
        self.code_input.setFixedWidth(490)

        # Кнопка активации
        self.activate_button = QPushButton("Активировать")
        self.activate_button.clicked.connect(lambda: self.activate_code("input"))
        self.activate_button.setFixedWidth(490)
        
        # Список активированных дополнений
        self.addons_list = QListWidget()
        self.addons_list.setFixedWidth(490)

        self.addons_list.currentItemChanged.connect(self.show_description)

        # Кнопка деактивации
        self.deactivate_button = QPushButton("Деактивировать")
        self.deactivate_button.clicked.connect(self.deactivate_selected)

        # Архив
        self.archive_list = QTableWidget()
        self.archive_list.setColumnCount(2)
        self.archive_list.setHorizontalHeaderLabels(["Название", "Код активации"])
        self.archive_list.setFixedWidth(490)
        self.archive_clear_button = QPushButton("Очистить архив")

        self.archive_clear_button.clicked.connect(self.clear_archive)
        self.archive_list.currentItemChanged.connect(self.show_description)

        # Существующие
        self.all_addons_list = QTableWidget()
        self.all_addons_list.setColumnCount(2)
        self.all_addons_list.setHorizontalHeaderLabels(["Название", "Код активации"])
        self.all_addons_list.setFixedWidth(490)
        self.description_browser = QTextBrowser()
        self.description_browser.setFixedSize(490, 120)
        self.activate_selected_button = QPushButton("Активировать выбранное")

        self.activate_selected_button.clicked.connect(lambda: self.activate_code("selected"))
        self.all_addons_list.currentItemChanged.connect(self.show_description)

        # Активация
        activation_group = QGroupBox("Активация дополнений")
        activation_layout = QVBoxLayout(activation_group)
        activation_layout.addWidget(QLabel("Поле для ввода"))
        activation_layout.addWidget(self.code_input)
        activation_layout.addWidget(self.activate_button)
        activation_layout.addStretch(1)
        activation_layout.addWidget(QLabel("Описание дополнения"))
        activation_layout.addWidget(self.description_browser)
        

        # Активированные
        activated_group = QGroupBox("Активированные дополнения")
        activated_layout = QVBoxLayout(activated_group)
        activated_layout.addWidget(self.addons_list)
        activated_layout.addWidget(self.deactivate_button, alignment=Qt.AlignRight | Qt.AlignTop)

        # Архивированные
        archive_group = QGroupBox("Архив дополнений")
        archive_layout = QVBoxLayout(archive_group)
        archive_layout.addWidget(self.archive_list)
        archive_layout.addWidget(self.archive_clear_button, alignment=Qt.AlignRight)

        # Существующие
        existent_group = QGroupBox("Существующие дополнения")
        existent_layout = QVBoxLayout(existent_group)
        existent_layout.addWidget(self.all_addons_list)
        existent_layout.addWidget(self.activate_selected_button, alignment=Qt.AlignRight)

        # Размещаем в grid
        grid.addWidget(activation_group, 0, 0)
        grid.addWidget(existent_group, 0, 1, 2, 1)
        grid.addWidget(activated_group, 0, 2)
        grid.addWidget(archive_group, 1, 2)
        self.layout.addLayout(grid)
        self.update_addons_list()

    def on_image_loaded(self, pixmap):
        """Вызывается, когда картинка успешно загружена"""
        self.image_label.setPixmap(pixmap)
        self.image_label.setText("") # Убираем текст "Загрузка"

    def on_image_error(self):
        """Вызывается при ошибке"""
        self.image_label.setText("Ошибка загрузки")
        self.image_label.setStyleSheet("color: red;")

    def activate_code(self, source):
        """Обработка ввода кода активации"""
        if source == "input":
            code = self.code_input.text().strip()
        elif source == "selected":
            selected = self.all_addons_list.currentItem()
            if not selected:
                return
            code = selected.data(Qt.UserRole)

        # Если поле не пустое
        if code:
            if code not in self.addons_manager.addons:
                QMessageBox.warning(self, "Ошибка", "Дополнение не найдено!")
                return
            
            # Попытка
            if self.addons_manager.activate_addon(code):
                QMessageBox.information(self, "Успех", f"Дополнение '{code}' активировано!") # Успех - сообщение
                self.code_input.clear() # Очищаем поле ввода
                self.addon_activated.emit(code, True) # Подаем сигнал
                self.update_addons_list() # Обновляем список
            else:
                QMessageBox.warning(self, "Ошибка", "Это дополнение уже активировано!") # Уже активировано - предупреждение

    def update_addons_list(self):
        """Обновляет список аддонов"""
        # Активированные
        self.addons_list.clear()
        for addon in self.addons_manager.get_active_addons():
            item = QListWidgetItem(self.addons_manager.addons[addon]["name"])
            item.setData(Qt.UserRole, addon)
            self.addons_list.addItem(item)

        # Архив
        self.archive_list.clear()
        self.archive_list.setRowCount(len(self.addons_manager.default_addons))
        row = 0
        for addon in self.addons_manager.get_archive_addons():
            item = QTableWidgetItem(self.addons_manager.addons[addon]["name"])
            item.setData(Qt.UserRole, addon)
            activation_code = self.addons_manager.addons[addon]
            self.archive_list.setItem(row, 0, QTableWidgetItem(item))
            self.archive_list.setItem(row, 1, QTableWidgetItem(self.addons_manager.default_addons[addon]))

        # Существующие
        #self.all_addons_list.clear()
        #for addon in self.addons_manager.get_all_addons():
        #    item = QListWidgetItem(self.addons_manager.addons[addon]["name"])
        #    item.setData(Qt.UserRole, addon)
        #    self.all_addons_list.addItem(item)

    def deactivate_selected(self):
        """Деактивирует дополнение"""
        selected = self.addons_list.currentItem()

        if selected:
            code = selected.data(Qt.UserRole)
            if self.addons_manager.deactivate_addon(code):
                QMessageBox.information(self, "Успех", f"Дополнение '{code}' деактивировано!")
                self.addon_activated.emit(code, False) # Подаем сигнал
                self.update_addons_list() # Обновляем список

    def show_description(self, current):
        if current:
            # Получаем код из данных элемента
            code = current.data(Qt.UserRole)
            if code in self.addons_manager.addons:
                self.description_browser.setText(
                    self.addons_manager.addons[code]["description"]
                )

    def clear_archive(self):
        """Очищает архив дополнений"""
        for code in self.addons_manager.addons:
            if self.addons_manager.addons[code]["ever_activated"] and not self.addons_manager.addons[code]["enabled"]:
                self.addons_manager.addons[code]["ever_activated"] = False
        self.addons_manager.save_addons()
        self.update_addons_list()