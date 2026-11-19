# Перенос проекта FRI

Распакуйте ZIP и откройте папку fri-site в PowerShell. В архиве есть история Git, текущие незакоммиченные правки, материалы дизайна, рабочая база db.sqlite3 и фото в private-media/.

## Windows x64

Установите 64-битный Python 3.14 и выполните из папки fri-site:

    py -3.14 -m venv .venv
    .\.venv\Scripts\python.exe -m pip install --no-index --find-links .\transfer-wheels -r requirements-transfer.txt
    .\.venv\Scripts\python.exe manage.py migrate
    .\.venv\Scripts\python.exe manage.py runserver 127.0.0.1:8000

Откройте http://127.0.0.1:8000/ или http://127.0.0.1:8000/zxc/. Если py недоступен, используйте python -m venv .venv после проверки версии. Зависимости для Windows x64 устанавливаются из архива без интернета.

## Linux или macOS

Используйте Python 3.14 и выполните:

    python3.14 -m venv .venv
    .venv/bin/python -m pip install -r requirements-transfer.txt
    .venv/bin/python manage.py migrate
    .venv/bin/python manage.py runserver 127.0.0.1:8000

Здесь для установки зависимостей нужен интернет.

## Продолжение работы

При упаковке Django check и миграции прошли. Три из 53 тестов Django упали на проверках текущей разметки.

- Откройте fri-site в Codex или редакторе. Контекст проекта есть в CURRENT-STATE.md, PROJECT-CONTEXT.md и KNOWN-ISSUES.md.
- Установите Git и выполните git status, чтобы увидеть перенесённые правки. У репозитория сохранён origin.
- Для пустой базы переименуйте db.sqlite3 при остановленном сервере и запустите migrate. Для нового администратора используйте manage.py createsuperuser.
- Храните ZIP приватно, поскольку он содержит локальную базу и фото. Кэши, прежнее виртуальное окружение и файлы .env исключены. Для настроек публикации используйте .env.example.
