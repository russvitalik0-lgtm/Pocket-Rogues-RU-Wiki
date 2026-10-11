# saved_manager.py
import json
import os
from PyQt5.QtCore import QObject, pyqtSignal

class SavedManager(QObject):
    # Сигнал для уведомления интерфейса
    saved_changed = pyqtSignal() # Изменение списка сохраненных - обновление карточек

    def __init__(self, parent=None):
        super().__init__(parent)

        # Определяем путь к файлу
        current_dir = os.path.dirname(os.path.abspath(__file__))
        self.saved_file = os.path.join(current_dir, "saved_pages.json")

        # Загружаем список
        self.saved_pages = self.load_saved()

    def load_saved(self):
        """Загружает список сохраненных страниц из JSON"""
        try:
            with open(self.saved_file, "r", encoding="utf-8") as f:
                data = json.load(f)
                return data.get("saved_pages", [])
        except FileNotFoundError:
            return []
        except (json.JSONDecodeError, KeyError):
            return []

    def save_saved(self):
        """Сохраняет список сохраненных страниц в JSON"""
        with open(self.saved_file, "w", encoding="utf-8") as f:
            json.dump(
                {"saved_pages": self.saved_pages},
                f,
                ensure_ascii=False,
                indent=4
            )

    def add_page(self, page_id):
        """Добавляет страницу в сохраненные"""
        if page_id in self.saved_pages:
            return

        self.saved_pages.insert(0, page_id)

        self.save_saved()
        self.saved_changed.emit()

    def remove_page(self, page_id):
        """Удаляет страницу из сохранённых"""
        if page_id not in self.saved_pages:
            return

        self.saved_pages.remove(page_id)

        self.save_saved()
        self.saved_changed.emit()

    def is_saved(self, page_id):
        """Проверяет, сохранена ли страница"""
        return page_id in self.saved_pages

    def toggle(self, page_id):
        """Переключатель"""
        if self.is_saved(page_id):
            self.remove_page(page_id)
        else:
            self.add_page(page_id)