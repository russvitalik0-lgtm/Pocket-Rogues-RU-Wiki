# DraftManager
import json
from pathlib import Path
from datetime import datetime

class DraftManager:
    """
    Менеджер черновиков редактора.
    Хранит промежуточные версии редактируемых ранее файлов в папке drafts/
    Метаданные вынесены в отдельный .json
    """

    def __init__(self, wiki_dir):
        self.wiki_dir = Path(wiki_dir)
        self.drafts_dir = self.wiki_dir / "drafts"
        self.meta_file = self.drafts_dir / "drafts_meta.json"
        self.drafts_dir.mkdir(exist_ok=True)

    def _load_meta(self):
        """Загружает метаданные из drafts_meta.json"""
        if not self.meta_file.exists():
            return {}
        try:
            return json.loads(self.meta_file.read_text(encoding="utf-8"))
        except (json.JSONDecodeError, OSError):
            return {}

    def _save_meta(self, meta):
        """Сохраняет метаданные"""
        self.meta_file.write_text(
            json.dumps(meta, ensure_ascii=False, indent=4),
            encoding="utf-8"
        )

    def save_draft(self, original_name, content):
        """
        Сохраняет черновик для файла
        original_name - имя оригинала ('necromancer.html')
        content - содержимое черновика
        """
        draft_name = f"{original_name}.draft"
        draft_path = self.drafts_dir / draft_name
        draft_path.write_text(content, encoding="utf-8")

        # Обновляем метаданные
        meta = self._load_meta()
        original_path = self.wiki_dir / original_name
        original_mtime = original_path.stat().st_mtime if original_path.exists() else 0

        meta[original_name] = {
            "draft_file": draft_name,
            "saved_at": datetime.now().isoformat(timespec="seconds"),
            "original_modified_at": datetime.fromtimestamp(original_mtime).isoformat(timespec="seconds") if original_mtime else None,
        }
        self._save_meta(meta)

    def load_draft(self, original_name):
        """Загружает черновик. Возвращает (content, saved_at) или (None, None)"""
        meta = self._load_meta()
        entry = meta.get(original_name)
        if not entry:
            return None, None

        draft_path = self.drafts_dir / entry["draft_file"]
        if not draft_path.exists():
            return None, None

        content = draft_path.read_text(encoding="utf-8")
        return content, entry.get("saved_at")

    def delete_draft(self, original_name):
        """Удаляет черновик и запись в метаданных"""
        meta = self._load_meta()
        entry = meta.pop(original_name, None)
        if entry:
            draft_path = self.drafts_dir / entry["draft_file"]
            if draft_path.exists():
                draft_path.unlink()
            self._save_meta(meta)

    def has_draft(self, original_name):
        """Проверяет, есть ли черновик для файла"""
        meta = self._load_meta()
        entry = meta.get(original_name)
        if not entry:
            return False
        draft_path = self.drafts_dir / entry["draft_file"]
        return draft_path.exists()

    def get_draft_info(self, original_name):
        """Возвращает метаданные черновика (или None)"""
        meta = self._load_meta()
        return meta.get(original_name)
