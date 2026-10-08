# Pocket Rogues: RU-Wiki

Десктопная версия википедии по игре Pocket Rogues, написанная одним из Главных Редакторов на Python + PyQt5.

## Установка и запуск (в период отсутствия .exe-файла)

### 1. Клонировать репозиторий

```bash
git clone https://github.com/russvitalik0-lgtm/Pocket-Rogues-RU-Wiki.git
cd Pocket-Rogues-RU-Wiki
```

### 2. Создать виртуальное окружение

```bash
python -m venv .venv
```

### 3. Активировать окружение

**Windows (PowerShell):**
```powershell
Set-ExecutionPolicy -Scope CurrentUser -ExecutionPolicy RemoteSigned # Получение прав во избежание ругательств
.venv\Scripts\Activate.ps1
```

**Windows (cmd)**
```cmd
.venv\Scripts\activate.bat
```

**Linux / macOS:**
```bash
source .venv/bin/activate
```

### 4. Установить зависимости

```bash
pip install -r requirements.txt
```

### 5. Запустить

```bash
python Main.py
```

## Зависимости

- Python 3.10+
- PyQt5
- PyQtWebEngine
- markdown
- requests

## Структура проекта

- `Main.py` - точка входа
- `pages/` - модули страниц приложения
- `pages/WikiContent/` - содержимое страниц вики (HTML)

## Лицензия

Отсутствует.