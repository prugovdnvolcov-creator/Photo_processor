# Подробная инструкция по установке photo_agent локально

## 📋 Предварительные требования

У вас уже установлены:
- ✅ VS Code
- ✅ Node.js (не требуется для этого проекта, но не помешает)
- ✅ Git

**Дополнительно потребуется:**
- Python 3.8 или выше (проверьте версию)

---

## 🔧 ШАГ 1: Проверка версии Python

### На Windows:
1. Откройте командную строку (cmd) или PowerShell
2. Введите команду:
   ```bash
   python --version
   ```
   или
   ```bash
   python3 --version
   ```

### На macOS/Linux:
1. Откройте терминал
2. Введите команду:
   ```bash
   python3 --version
   ```

**Если Python не установлен:**
- Скачайте с официального сайта: https://www.python.org/downloads/
- **Важно для Windows:** При установке отметьте галочку ✅ "Add Python to PATH"

---

## 📥 ШАГ 2: Клонирование репозитория

### Вариант А: Если у вас есть ссылка на репозиторий

1. Откройте терминал (macOS/Linux) или PowerShell/cmd (Windows)
2. Перейдите в папку, где хотите хранить проект:
   ```bash
   cd Documents/Projects
   ```
   или
   ```bash
   cd C:\Users\ВашеИмя\Documents\Projects
   ```

3. Склонируйте репозиторий:
   ```bash
   git clone <URL_репозитория>
   ```

### Вариант Б: Если код уже в папке /workspace

Пропустите этот шаг — код уже доступен в папке `photo_agent`

---

## 🗂️ ШАГ 3: Открытие проекта в VS Code

1. Запустите VS Code
2. Нажмите `File` → `Open Folder...` (или `Ctrl+K Ctrl+O`)
3. Выберите папку `photo_agent`
4. VS Code может предложить установить расширения для Python — согласитесь

**Рекомендуемые расширения для VS Code:**
- Python (от Microsoft)
- Pylance
- Black Formatter

---

## 🐍 ШАГ 4: Создание виртуального окружения

**Зачем это нужно:** Виртуальное окружение изолирует зависимости проекта от других ваших проектов.

### На Windows (PowerShell):

```powershell
# Перейдите в папку проекта
cd photo_agent

# Создайте виртуальное окружение
python -m venv venv

# Активируйте его
.\venv\Scripts\Activate.ps1
```

**Если PowerShell блокирует выполнение скриптов:**
```powershell
Set-ExecutionPolicy -ExecutionPolicy RemoteSigned -Scope CurrentUser
```

### На Windows (cmd):

```cmd
cd photo_agent
python -m venv venv
venv\Scripts\activate.bat
```

### На macOS/Linux:

```bash
cd photo_agent
python3 -m venv venv
source venv/bin/activate
```

**✅ Как понять, что окружение активировано:**
В начале строки терминала появится `(venv)`, например:
```
(venv) user@computer photo_agent %
```

---

## 📦 ШАГ 5: Установка зависимостей

Теперь установим все необходимые библиотеки.

### Вариант А: Базовая установка (рекомендуется для начала)

```bash
pip install -e .
```

**Что делает эта команда:**
- `-e` означает "editable" — вы сможете изменять код и видеть изменения сразу
- Устанавливает все зависимости из `pyproject.toml`

### Вариант Б: Установка с инструментами для разработки

```bash
pip install -e ".[dev]"
```

**Дополнительно устанавливает:**
- `pytest` — для запуска тестов
- `black` — автоматическое форматирование кода
- `flake8` — проверка стиля кода
- `mypy` — проверка типов

### Что будет установлено:

| Пакет | Назначение |
|-------|-----------|
| `numpy` | Работа с массивами данных |
| `opencv-python` | Обработка изображений |
| `Pillow` | Работа с изображениями |
| `rembg` | Удаление фона с изображений |
| `requests` | HTTP-запросы |
| `transformers` | AI-модели (CLIP) |
| `torch` | PyTorch (фреймворк для нейросетей) |
| `gdown` | Скачивание из Google Drive |

⏱️ **Время установки:** 5-15 минут (зависит от скорости интернета, torch — большой пакет)

---

## ✅ ШАГ 6: Проверка установки

### Проверка 1: Убедитесь, что пакет установлен

```bash
pip list | grep photo-agent
```

Или на Windows:
```bash
pip list | findstr photo-agent
```

Должно появиться что-то вроде:
```
photo-agent    1.0.7
```

### Проверка 2: Запуск тестов

```bash
pytest
```

Вы должны увидеть результат выполнения тестов. Если все тесты прошли успешно — установка корректна.

### Проверка 3: Запуск CLI

```bash
photo-agent
```

Или альтернативно:
```bash
python -m photo_agent.src.cli
```

---

## 🎯 ШАГ 7: Настройка структуры папок

Создайте папку для базы знаний (если планируете использовать):

```bash
mkdir knowledge_base
mkdir knowledge_base/PLATE
mkdir knowledge_base/PRODUCT
mkdir knowledge_base/LIFESTYLE
```

**Зачем это нужно:** В эти папки можно добавлять примеры изображений для обучения классификатора.

---

## 🚀 ШАГ 8: Первое использование

### Пример использования как библиотеки:

Создайте файл `test_run.py` в корне проекта:

```python
from photo_agent.src import Processor, setup_logging

# Инициализация
logger = setup_logging()
processor = Processor(knowledge_base_dir="knowledge_base")

# Обработка изображения
processed_img, context_type = processor.process("input.jpg")
if processed_img:
    processed_img.save("output.png")
    print(f"Context: {context_type}")
```

### Использование через командную строку:

```bash
photo-agent
```

Запустится интерактивный интерфейс.

---

## ⚙️ ШАГ 9: Настройка конфигурации (при необходимости)

Все настройки находятся в файле `src/core/config.py`

**Основные параметры:**

| Параметр | Значение по умолчанию | Описание |
|----------|---------------------|----------|
| `CANVAS_W` | 1280 | Ширина выходного изображения |
| `CANVAS_H` | 840 | Высота выходного изображения |
| `PRODUCT_BG_COLOR` | #FAFAFA | Цвет фона |
| `AI_CONFIDENCE_THRESHOLD` | 0.80 | Минимальная уверенность AI |
| `SIMILARITY_THRESHOLD` | 0.92 | Порог схожести для базы знаний |

---

## 🛠️ Решение распространённых проблем

### Проблема 1: Ошибка при установке torch

**Решение:** Установите torch отдельно с официального сайта:
```bash
pip install torch --index-url https://download.pytorch.org/whl/cu118
```
(для CPU без CUDA уберите `--index-url`)

### Проблема 2: Ошибка "ModuleNotFoundError"

**Решение:** Убедитесь, что виртуальное окружение активировано:
```bash
# Должно быть (venv) в начале строки
(venv) $ python your_script.py
```

### Проблема 3: Медленная загрузка моделей

**Решение:** При первом запуске модели CLIP загружаются из интернета (~500MB). Последующие запуски будут быстрее.

### Проблема 4: Ошибки с opencv на macOS

**Решение:**
```bash
pip uninstall opencv-python
pip install opencv-python-headless
```

### Проблема 5: Конфликты версий Python

**Решение:** Используйте конкретную версию:
```bash
python3.11 -m venv venv
```

---

## 📝 Быстрая шпаргалка команд

```bash
# Активация виртуального окружения
# Windows (PowerShell): .\venv\Scripts\Activate.ps1
# macOS/Linux: source venv/bin/activate

# Установка зависимостей
pip install -e .

# Запуск тестов
pytest

# Запуск программы
photo-agent

# Деактивация окружения
deactivate
```

---

## 🎓 Дополнительные ресурсы

- Документация: см. `README.md`
- Тесты: папка `tests/`
- Исходный код: папка `src/`

---

## ✅ Чек-лист успешной установки

- [ ] Python 3.8+ установлен и проверен
- [ ] Проект открыт в VS Code
- [ ] Виртуальное окружение создано (`venv/` папка существует)
- [ ] Виртуальное окружение активировано (виден префикс `(venv)`)
- [ ] Зависимости установлены (`pip install -e .` выполнено без ошибок)
- [ ] Тесты проходят (`pytest` выполняется успешно)
- [ ] Команда `photo-agent` запускается

**Поздравляем! Установка завершена успешно! 🎉**
