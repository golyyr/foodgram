# Foodgram

Сервис для публикации рецептов: пользователи делятся блюдами, подписываются
друг на друга, собирают избранное и список покупок.

Документация задания: [Foodgram](https://github.com/yandex-praktikum/foodgram-project-react/blob/master/README.md).  
После запуска: [документация Redoc](http://localhost/api/docs/).

## Продакшен

- [Сайт](https://158.160.159.158)
- [Админка](https://158.160.159.158/admin/)
- [Документация API](https://158.160.159.158/api/docs/)

## Технологический стек

- Python 3.11, Django 4.2, Django REST Framework, Djoser, django-filter
- PostgreSQL 16
- Gunicorn
- Docker, Docker Compose
- Nginx
- React (готовый фронтенд из прекода)
- GitHub Actions, Docker Hub

## Запуск в Docker

```bash
git clone https://github.com/golyyr/foodgram.git
cd foodgram/infra
cp .env.example .env
# заполните SECRET_KEY, POSTGRES_PASSWORD и при необходимости ALLOWED_HOSTS
docker compose up -d --build
```

- [Сайт](http://localhost)
- [Документация API](http://localhost/api/docs/)
- [Админка](http://localhost/admin/)

Контейнер `frontend` только собирает статику и завершается. В рабочем составе
остаются nginx, PostgreSQL и Django + Gunicorn. Статика и медиа раздаются
nginx, данные хранятся в volumes.

### Импорт продуктов и тегов

Команды выполняются автоматически при старте backend. При необходимости
вручную внутри контейнера:

```bash
docker compose exec backend python manage.py import_products
docker compose exec backend python manage.py import_tags
```

Можно указать свой путь к фикстуре:

```bash
docker compose exec backend python manage.py import_products --fixture /app/data/ingredients.json
docker compose exec backend python manage.py import_tags --fixture /app/data/tags.json
```

Создание суперпользователя:

```bash
docker compose exec backend python manage.py createsuperuser
```

## Локальный запуск без Docker

Нужны Python 3.11+, PostgreSQL и Node.js для сборки фронтенда.

1. Клонировать репозиторий и перейти в него:

```bash
git clone https://github.com/golyyr/foodgram.git
cd foodgram
```

2. Создать и активировать виртуальное окружение, установить зависимости:

```bash
python -m venv .venv
source .venv/bin/activate   # Windows: .venv\Scripts\activate
pip install -r backend/requirements.txt
```

3. Создать базу PostgreSQL и переменные окружения (или `.env` в `backend/`):

```bash
export POSTGRES_DB=foodgram
export POSTGRES_USER=foodgram
export POSTGRES_PASSWORD=foodgram
export DB_HOST=localhost
export DB_PORT=5432
export SECRET_KEY=dev-secret
export DEBUG=True
export ALLOWED_HOSTS=localhost,127.0.0.1
export CSRF_TRUSTED_ORIGINS=http://localhost:8000
```

4. Применить миграции и импортировать фикстуры:

```bash
cd backend
python manage.py migrate
python manage.py import_products --fixture ../data/ingredients.json
python manage.py import_tags --fixture ../data/tags.json
python manage.py createsuperuser
python manage.py runserver
```

API будет доступен по адресу [http://127.0.0.1:8000](http://127.0.0.1:8000).  
Админка: [http://127.0.0.1:8000/admin/](http://127.0.0.1:8000/admin/).

5. Собрать фронтенд (в другом терминале):

```bash
cd frontend
npm install
npm run build
```

## CI/CD

При пуше в `main` workflow [`.github/workflows/foodgram.yml`](.github/workflows/foodgram.yml)
собирает образ backend, публикует его в Docker Hub как
`<user>/foodgram_backend:latest` и обновляет контейнеры на сервере.

В [секретах](https://docs.github.com/en/actions/security-guides/using-secrets-in-github-actions)
репозитория должны быть `DOCKER_USERNAME`, `DOCKER_PASSWORD` и `SSH_PRIVATE_KEY`.


## Автор

Антон Субботин — [golyyr](https://github.com/golyyr)  
Почта: [subbotin_antoshka@mail.ru](mailto:subbotin_antoshka@mail.ru)  
Telegram: [@lieutenant_priboy](https://t.me/lieutenant_priboy)
