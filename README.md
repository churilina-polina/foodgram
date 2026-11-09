# Foodgram

Foodgram — сайт для публикации рецептов. Пользователи могут публиковать свои
рецепты, добавлять чужие рецепты в избранное, подписываться на других авторов
и формировать список покупок с автоматическим суммированием ингредиентов по
всем рецептам, добавленным в список.

Проект разворачивался на облачном сервере (https://foodgram-polina.duckdns.org/),
сейчас демо-сервер выключен. Весь проект запускается локально одной командой:
см. раздел «Локальный запуск всего проекта в Docker» ниже.

Для развёртывания использовался бесплатный домен DuckDNS и системный nginx на
сервере (вне Docker), который терминирует HTTPS (сертификат Let's Encrypt) и
проксирует на контейнер `gateway`. Контейнер слушает нестандартный порт 9090,
потому что сервер был общим для нескольких учебных проектов, и порт 80 был занят
системным nginx для другого проекта.

## Технологии

- Python 3.11, Django 4.2, Django REST Framework
- Djoser + токен-аутентификация
- PostgreSQL
- Nginx, Gunicorn
- Docker, Docker Compose
- GitHub Actions (CI/CD)
- React (готовый фронтенд)

## Структура проекта

- `backend/` — Django-проект (REST API)
- `frontend/` — React-приложение (SPA)
- `infra/` — конфигурация nginx, docker-compose для локального запуска
  (`docker-compose.yml`) и для продакшен-сервера (`docker-compose.production.yml`,
  использует готовые образы из Docker Hub)
- `docs/` — спецификация API (OpenAPI/Redoc)
- `data/` — исходный список ингредиентов (json/csv)
- `.github/workflows/main.yml` — CI/CD: линтер, сборка и публикация образов
  в Docker Hub, деплой на сервер по SSH

## Локальный запуск бэкенда без Docker (для разработки)

```bash
cd backend
python3 -m venv venv
source venv/bin/activate          # Windows: venv\Scripts\activate
pip install -r requirements.txt
cp .env.example .env              # и отредактируйте при необходимости
python manage.py migrate
python manage.py load_ingredients
python manage.py createsuperuser
python manage.py create_test_data # теги, тестовые пользователи и рецепты
python manage.py runserver
```

API будет доступен на `http://127.0.0.1:8000/api/`, админка — на
`http://127.0.0.1:8000/admin/`.

## Локальный запуск всего проекта в Docker

```bash
cd infra
cp .env.example .env
docker compose up --build
```

- Фронтенд: `http://localhost/`
- API: `http://localhost/api/`
- Документация API: `http://localhost/api/docs/`
- Админка: `http://localhost/admin/`

Файл `.env` создаётся из шаблона `.env.example`, значений-заглушек достаточно
для локального запуска. После первого старта создайте суперпользователя и
тестовые данные:

```bash
docker compose exec backend python manage.py createsuperuser
docker compose exec backend python manage.py create_test_data
```

(Ингредиенты и миграции применяются автоматически при каждом старте
контейнера `backend`.)

## Деплой на удалённый сервер

Подробная пошаговая инструкция — в разделе, который был предоставлен
отдельно при настройке проекта (Docker Hub, секреты GitHub Actions, nginx
на сервере). Кратко:

1. На сервере устанавливаются Docker и Docker Compose.
2. На сервере создаётся директория `foodgram/infra/`, куда GitHub Actions
   копирует `docker-compose.production.yml`. Рядом нужно создать файл
   `.env` (см. `infra/.env.example` в репозитории).
3. GitHub Actions при пуше в ветку `main` собирает образы `backend`,
   `frontend` и `gateway`, публикует их в Docker Hub и разворачивает проект
   на сервере по SSH.
4. Контейнер `gateway` публикуется на порту, указанном в `ports` сервиса
   `gateway` в `infra/docker-compose.production.yml` (в этом проекте — 9090).
   Если порт 80 на сервере свободен, туда же можно поставить `"80:80"`.

## Автор

[churilina-polina](https://github.com/churilina-polina)
