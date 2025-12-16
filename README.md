# bollard_ims

Платформа для управления документами СМК (загрузка/версионирование/поиск/скачивание) с аутентификацией и ролями. Бэкенд на FastAPI, хранение метаданных в SQLite (можно заменить на PostgreSQL), файлы на диске (можно заменить на S3/MinIO).

## Быстрый старт (локально)

```bash
python -m venv .venv
source .venv/bin/activate
pip install -r requirements-dev.txt
uvicorn app.main:app --reload
```

API доступно на `http://localhost:8000` (Swagger UI: `/docs`). При первом запуске автоматически создаётся админ `admin/admin123`.

## Основные возможности
- Регистрация/логин, роли admin/user.
- Админ может загружать документы и создавать версии.
- Пользователь может искать, просматривать метаданные и скачивать версии.
- Фильтры по названию/описанию/тегам.
- Endpoint для списка версий и скачивания конкретной версии.

## Тесты и линтинг

```bash
pytest
ruff check .
```

## GitHub Actions
- Workflow `ci.yml` выполняет линт Ruff и тесты pytest.
- Секреты (например, `SECRET_KEY`, `DATABASE_URL`, `STORAGE_DIR`) можно задавать в GitHub Environments/Secrets; по умолчанию используется SQLite и локальное хранилище.

## Замена хранилищ
- База данных: установите `DATABASE_URL=postgresql+psycopg2://...` и добавьте драйвер `psycopg2-binary` в зависимости.
- Файлы: можно заменить `storage.storage` на S3/MinIO клиент, оставив интерфейс `save/get_path`.
