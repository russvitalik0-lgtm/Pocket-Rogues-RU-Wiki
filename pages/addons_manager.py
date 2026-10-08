# AddonsManager
import json
import os

class AddonsManager:
    def __init__(self):
        # Получаем путь к папке, где находится файл
        current_dir = os.path.dirname(os.path.abspath(__file__))
        self.settings_file = os.path.join(current_dir, "addons.json")

        self.default_addons = {
            "AddBrowser": {
                "enabled": False,
                "name": "Браузер",
                "description": "Добавляет вкладку с браузером",
                "ever_activated": False,
                "public": True,
                "tab_title": "Браузер"
            },
            "AddPrototype": {
                "enabled": False,
                "name": "Прототип заметок",
                "description": "Добавляет примеры работы с Markdown и HTML",
                "ever_activated": False,
                "public": True
            },
            "AddNotesV2": {
                "enabled": False,
                "name": "Расширенные заметки",
                "description": "Добавляет дополнительные функции заметок",
                "ever_activated": False,
                "public": True
            },
            "SupplierFeatures": {
                "enabled": False,
                "name": "Спец. функции для Поставщиков",
                "ever_activated": False,
                "description": "Добавляет дополнительные функции для структурирования информации. Специализировано для Поставщиков.",
                "public": False,
                "tab_title": "Спец. функции"
            }
        }
        self.ensure_file_exists()
        self.addons = self.load_addons()

    def ensure_file_exists(self):
        """Создает файл addons.json, если он отсутствует"""
        if not os.path.exists(self.settings_file):
            with open(self.settings_file, "w", encoding="utf-8") as f:
                json.dump(self.default_addons, f, ensure_ascii=False, indent=4)

    def load_addons(self):
        """Загружает словарь дополнений из файла"""
        with open(self.settings_file, "r", encoding="utf-8") as f:
            return json.load(f)

    def save_addons(self):
        """Сохраняет список активированных дополнений"""
        with open(self.settings_file, "w", encoding="utf-8") as f:
            json.dump(self.addons, f, ensure_ascii=False, indent=4)

    def activate_addon(self, code):
        """Активирует дополнения по коду"""
        if code in self.addons:
            if not self.addons[code]["enabled"]:
                self.addons[code]["enabled"] = True
                self.addons[code]["ever_activated"] = True
                self.save_addons()
                return True
        return False

    def deactivate_addon(self, code):
        """Деактивирует дополнение"""
        if code in self.addons:
            if self.addons[code]["enabled"]:
                self.addons[code]["enabled"] = False
                self.save_addons()
                return True
        return False

    def is_active(self, code):
        """Проверяет, активно ли дополнение"""
        return code in self.addons and self.addons[code]["enabled"]

    def get_active_addons(self):
        """Возвращает список активных дополнений"""
        return [code for code, info in self.addons.items() if info["enabled"]]

    def get_all_addons(self):
        """Возвращает все дополнения"""
        return [code for code, info in self.addons.items() if info["public"]]

    def get_archive_addons(self):
        """Возвращает дополнения, которые были когда-либо активированы, но выключены на данный момент"""
        return [
            code for code, info in self.addons.items()
            if info["ever_activated"] and not info["enabled"]
        ]

class AddonsRegistry:
    def __init__(self):
        self.addon_tabs = {
            "AddPrototype": [
                {"title": "Прототип", "widget": self.create_prototype_tab}
            ],
            "AddNotesV2": [
                {"title": "Ver 2.0", "widget": self.create_v2_tab},
                {"action": "rename_default", "title": "Ver 1.0"}
            ]
        }