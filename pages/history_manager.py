import json
import os
from PyQt5.QtCore import QObject, pyqtSignal
from PyQt5.QtWidgets import QMessageBox

class HistoryManager(QObject):
    # Сигналы для уведомления интерфейса об изменениях
    history_changed = pyqtSignal() # Изменение истории -- обновление карточек
    settings_changed = pyqtSignal() # Изменение настроек -- обновление интерфейса настроек

    def __init__(self, parent=None):
        super().__init__(parent)

        # Определяем путь к файлу настроек
        current_dir = os.path.dirname(os.path.abspath(__file__))
        self.settings_file = os.path.join(current_dir, "history_settings.json")

        # Загружаем настройки
        self.settings = self.load_settings()

        # История просмотров (список ID страниц)
        self.recent_pages = self.settings.get("recent_pages", [])

    def load_settings(self):
        """Загружает настройки из JSON"""
        # Настройки по умолчанию
        default_settings = {
            "save_history": True, # Сохранять историю
            "limit": 10, # Лимит страниц
            "recent_pages": [] # Пустой список истории
        }

        try:
            with open(self.settings_file, "r", encoding="utf-8") as f:
                settings = json.load(f)
                # Обновляем данные "По умолчанию" на загруженные
                default_settings.update(settings)
        except FileNotFoundError:
            # Если файл не найден, используем настройки по умолчанию
            QMessageBox.information(
                None,
                "Файл настроек не найден",
                "Будет создан новый файл с настройками по умолчанию."
            )
            pass

        return default_settings

    def save_settings(self):
        """Сохраняет настройки в JSON"""
        # Обновляем данные в настройках
        self.settings["recent_pages"] = self.recent_pages

        # Сохраняем в файл
        with open(self.settings_file, "w", encoding="utf-8") as f:
            json.dump(self.settings, f, ensure_ascii=False, indent=4)

    def add_page(self, page_id):
        """Добавляет страницу в Историю Просмотра"""
        # Проверяем, включено ли сохранение истории
        if not self.settings["save_history"]:
            return
        
        # Удаляем страницу, если она уже есть в истории
        if page_id in self.recent_pages:
            self.recent_pages.remove(page_id)

        # Добавляем страницу в начало списка
        self.recent_pages.insert(0, page_id)

        # Обрезаем список до лимита
        limit = self.settings["limit"]
        if len(self.recent_pages) > limit:
            self.recent_pages = self.recent_pages[:limit]

        # Сохраняем наши изменения
        self.save_settings()

        # Уведомляем интерфейс об изменении
        self.history_changed.emit()

    def update_settings(self, save_history, limit):
        """Обновляет настройки"""
        # Обновляем значения
        self.settings["save_history"] = save_history
        self.settings["limit"] = limit

        # Если история отключена - очищаем ее
        if not save_history:
            self.recent_pages = []
        else:
            # Если включена - обрезаем до нового лимита
            self.recent_pages = self.recent_pages[:limit]

        # Сохраняем
        self.save_settings()

        # Уведомляем интерфейс
        self.settings_changed.emit()
        self.history_changed.emit()