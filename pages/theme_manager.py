# theme_manager.py
import json
import os
from PyQt5.QtCore import QObject, pyqtSignal

class ThemeManager(QObject):
    """Менеджер QSS-тем приложения"""

    theme_changed = pyqtSignal(str)

    # Доступные темы (совпадают с именами .qss файлов в themes/)
    AVAILABLE_THEMES = ["dark", "light"]
    DEFAULT_THEME = "dark"

    def __init__(self, app, parent=None):
        super().__init__(parent)
        self.app = app

        # Путь к папке themes
        current_dir = os.path.dirname(os.path.abspath(__file__))
        self.themes_dir = os.path.join(os.path.dirname(current_dir), "themes")

        # Путь к файлу настроек
        self.settings_file = os.path.join(current_dir, "theme_settings.json")

        # Загружаем сохранённую схему
        self.current_theme = self._load_theme()

    def _load_theme(self):
        """Загружает сохранённую тему из JSON. Если файла нет - дефолт"""
        try:
            with open(self.settings_file, "r", encoding="utf-8") as f:
                data = json.load(f)
                theme = data.get("theme", self.DEFAULT_THEME)
                # Проверяем, что тема вообще существует
                if theme not in self.AVAILABLE_THEMES:
                    return self.DEFAULT_THEME
                return theme
        except (FileNotFoundError, json.JSONDecodeError):
            return self.DEFAULT_THEME

    def _save_theme(self):
        """Сохраняет текущую тему в JSON"""
        with open(self.settings_file, "w", encoding="utf-8") as f:
            json.dump(
                {"theme": self.current_theme},
                f,
                ensure_ascii=False,
                indent=4
            )

    def apply_theme(self, theme_name):
        """Загружает QSS из themes/<theme_name>.qss и применяет"""
        if theme_name not in self.AVAILABLE_THEMES:
            print(f"Неизвестная тема: {theme_name}")
            return

        qss_path = os.path.join(self.themes_dir, f"{theme_name}.qss")
        try:
            with open(qss_path, "r", encoding="utf-8") as f:
                qss = f.read()
                self.app.setStyleSheet(qss)
                self.current_theme = theme_name
                self._save_theme()
                self.theme_changed.emit(theme_name)
        except FileNotFoundError:
            print(f"QSS-файл не найден: {qss_path}")

    def apply_current_theme(self):
        """Применяет сохранённую тему. Вызывается при старте"""
        self.apply_theme(self.current_theme)