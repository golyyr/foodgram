# Foodgram

Сервис публикации рецептов. Фронтенд отдаёт nginx, API и админка работают через Gunicorn, данные хранятся в PostgreSQL.

## Запуск

Из каталога `infra`:

```bash
cp .env.example .env
docker compose up -d --build
```

Сайт: `http://localhost`  
Документация API: `http://localhost/api/docs/`  
Админка: `http://localhost/admin/`

Контейнер `frontend` только собирает статику и завершается. В рабочем составе остаются nginx, PostgreSQL и Django + Gunicorn. Статика и медиа раздаются nginx, данные лежат в volumes.

## Учётные записи

Администратор:

- почта: `admin@foodgram.ru`
- пароль: `Adminpass123`

Тестовые пользователи (пароль у всех `Testpass123`):

- `vasya@foodgram.ru`
- `masha@foodgram.ru`
- `petya@foodgram.ru`

Ингредиенты, теги и рецепты загружаются при старте backend.

## CI/CD

При пуше в `main` workflow `.github/workflows/foodgram.yml` собирает образ backend, публикует его в Docker Hub как `<user>/foodgram_backend:latest` и обновляет контейнеры на сервере.

В секретах репозитория должны быть `DOCKER_USERNAME`, `DOCKER_PASSWORD` и `SSH_PRIVATE_KEY`.
