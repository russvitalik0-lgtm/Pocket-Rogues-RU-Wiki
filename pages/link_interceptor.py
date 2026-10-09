# Перехватчик внешних ссылок в эмуляторе Вики (QWebEngineView)
from PyQt5.QtWebEngineWidgets import QWebEnginePage
from PyQt5.QtCore import QUrl

BLACK_LIST = [
    "pocketrogues.fandom.com",
]

class InterceptingPage(QWebEnginePage):
    """Страница QWebEngineView с настраиваемой блокировкой ссылок"""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.block_external = True 
        self.on_external_link = None
        self.black_list = list(BLACK_LIST)

    def acceptNavigationRequest(self, url, type, isMainFrame):
        if not self.block_external: # Если блокировка выключена: 
            return super().acceptNavigationRequest(url, type, isMainFrame) # Пропускаем всё

        if url.scheme() not in ("http", "https"): # Все якоря и локальные файлы пропускаем всегда
            return super().acceptNavigationRequest(url, type, isMainFrame)

        host = url.host() # Fandom - Блокируем полностью
        if any(host == d or host.endswith("." + d) for d in self.black_list):
            return False

        if self.on_external_link:
            self.on_external_link(url)
        return False
