# syntax_highlighters.py
from PyQt6.QtCore import QRegularExpression
from PyQt6.QtGui import QSyntaxHighlighter, QTextCharFormat, QColor

class HtmlHighlighter(QSyntaxHighlighter):
    """Подсветка синтаксиса HTML в стиле VSCode (Dark+)"""

    def __init__(self, document):
        super().__init__(document)
        self.rules = []

        # --- Декларация <!-тегов ---
        doctype_format = QTextCharFormat()
        doctype_format.setForeground(QColor("#569cd6"))
        self.rules.append((
            QRegularExpression(r"<![a-zA-Z][^>]*>"),
            doctype_format
        ))

        # --- Комментарии: <!-- ... --> ---
        comment_format = QTextCharFormat()
        comment_format.setForeground(QColor("#6a9955"))
        self.rules.append((
            QRegularExpression(r"<!--[\s\S]*?-->"),
            comment_format
        ))

        # --- Теги целиком: <div>, </div>, <h1> и т.п. ---
        tag_format = QTextCharFormat()
        tag_format.setForeground(QColor("#569cd6"))
        self.rules.append((
            QRegularExpression(r"</?[a-zA-Z][^>]*/?>"),
            tag_format
        ))

        # --- Аттрибуты: class=, href=, src= ---
        attr_format = QTextCharFormat()
        attr_format.setForeground(QColor("#9cdcfe"))
        self.rules.append((
            QRegularExpression(r"[a-zA-Z-]+(?==)"),
            attr_format
        ))

        # Значения аттрибутов: "wiki-infobox" ---
        value_format = QTextCharFormat()
        value_format.setForeground(QColor("#ce9178"))
        self.rules.append((
            QRegularExpression(r'"[^"]*"'),
            value_format
        ))
        self.rules.append((
            QRegularExpression(r"'[^']*'"),
            value_format
        ))

        # --- Сущности: &nbsp; &amp; &lt; ---
        entity_format = QTextCharFormat()
        entity_format.setForeground(QColor("#d7ba7d"))
        self.rules.append((
            QRegularExpression(r"&[a-zA-Z]+;|&#\d+;"),
            entity_format
        ))

    def highlightBlock(self, text):
        """Применяет правила подсветки к блоку текста"""
        for pattern, fmt in self.rules:
            iterator = pattern.globalMatch(text)
            while iterator.hasNext():
                match = iterator.next()
                self.setFormat(match.capturedStart(), match.capturedLength(), fmt)

class CssHighlighter(QSyntaxHighlighter):
    """Подсветка синтаксиса CSS в стиле VSCode (Dark+)"""

    def __init__(self, document):
        super().__init__(document)
        self.rules = []

        # --- Комментарии: /* ... */ ---
        comment_format = QTextCharFormat()
        comment_format.setForeground(QColor("#6a9955"))
        self.rules.append((
            QRegularExpression(r"/\*[\s\S]*?\*/"),
            comment_format
        ))

        # --- ! important ---
        important_format = QTextCharFormat()
        important_format.setForeground(QColor("#569cd6"))
        important_format.setFontWeight(700)
        self.rules.append((
            QRegularExpression(r"!important"),
            important_format
        ))

        # --- Свойства: color:, background-color:, --var: ---
        # Ищет слово с дефисом или без, за которым идёт двоеточие
        property_format = QTextCharFormat()
        property_format.setForeground(QColor("#9cdcfe"))
        self.rules.append((
            QRegularExpression(r"(?<![\w-])-{0,2}[a-zA-Z][a-zA-Z0-9-]*(?=\s*:)"),
            property_format
        ))

        # --- Значения с # (hex-цвета), числа с единицами, ключевые слова ---
        # Проще: значения после двоеточия, до ; или }
        # Это сложно ловить регуляркой надёжно - подсветим ключевые значения
        value_format = QTextCharFormat()
        value_format.setForeground(QColor("#ce9178"))

        # HEX-цвета
        self.rules.append((
            QRegularExpression(r"#[0-9a-fA-F]{3,8}\b"),
            value_format
        ))

        # Числа с единицами (px, em, rem, % и т.п.)
        self.rules.append((
            QRegularExpression(r"\b\d+(\.\d+)?(px|em|rem|%|s|ms|vh|vw|pt|cm|mm)\b"),
            value_format
        ))

        # var(--name)
        self.rules.append((
            QRegularExpression(r"\bvar\b"),
            property_format
        ))

        # --- Ключевые слова в значениях ---
        keyword_format = QTextCharFormat()
        keyword_format.setForeground(QColor("#569cd6"))
        keywords = (
            r"\b(sans-serif|serif|monospace|cursive|fantasy|"
            r"bold|bolder|lighter|italic|oblique|"
            r"none|auto|inherit|initial|unset|revert|"
            r"fixed|absolute|relative|static|sticky|"
            r"block|inline|inline-block|flex|grid|"
            r"center|left|right|top|bottom|middle|"
            r"hidden|visible|scroll|collapse)\b"
        )
        self.rules.append((
            QRegularExpression(keywords),
            keyword_format
        ))

        # --- Числа без единиц (после двоеточия): margin, z-index ---
        self.rules.append((
            QRegularExpression(r"(?<=:\s)[^;{}\n]+"),
            value_format
        ))

        # --- Селекторы: .class, #id, tag ---
        # Селектор - это слово после { предыдущего } или в начале строки
        # Регулярками - можно, но грубо
        selector_format = QTextCharFormat()
        selector_format.setForeground(QColor("#d7ba7d"))

        # .class и #id
        self.rules.append((
            QRegularExpression(r"[.#][a-zA-Z_][a-zA-Z0-9_-]*"),
            selector_format
        ))

        # Теги (body, h1, a, div, ...) с опциональным псевдоклассом/псевдоэлементом
        self.rules.append((
            QRegularExpression(r"(?<![\w.#:\-])[a-zA-Z][a-zA-Z0-9]*(::?[a-zA-Z-]+)?(?=\s*[\s{,>+~\[]|$)"),
            selector_format
        ))

        # Псевдоклассы и псевдоэлементы (для .class:hover, #id:focus)
        self.rules.append((
            QRegularExpression(r"::?[a-zA-Z-]+"),
            selector_format
        ))

    def highlightBlock(self, text):
        """Применяет правила подсветки к блоку текста"""
        for pattern, fmt in self.rules:
            iterator = pattern.globalMatch(text)
            while iterator.hasNext():
                match = iterator.next()
                self.setFormat(match.capturedStart(), match.capturedLength(), fmt)
