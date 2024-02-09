#!/bin/bash
set -e

echo "Обновление кода"
git fetch
git pull

echo "Останавливаем Docker Compose"
docker-compose -f docker-compose.production.yaml down

echo "Запуска Docker Compose с файлом конфигурации production"
docker-compose -f docker-compose.production.yaml up -d --build

echo "Выполнение миграций в контейнере Django"
docker-compose -f docker-compose.production.yaml exec django python manage.py migrate --no-input

echo "Сбора статики в контейнере Django"
docker-compose -f docker-compose.production.yaml exec django python manage.py collectstatic --no-input

echo "Перезапуск контейнера Django для применения миграций и собранной статики"
docker-compose -f docker-compose.production.yaml restart django

echo "Перезапуск контейнера Nginx для применения обновленной конфигурации"
docker-compose -f docker-compose.production.yaml restart nginx

echo "Регистрация deploy в сервисе Rollbar"
commit_hash=$(git rev-parse HEAD)
source .env
export ROLLBAR_TOKEN

curl --http1.1 -X POST \
  https://api.rollbar.com/api/1/deploy \
  -H "X-Rollbar-Access-Token: $ROLLBAR_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"environment": "production", "revision": "'"$commit_hash"'", "local_username": "'"$USER"'", "comment": "Deployed new version", "status": "succeeded"}'

echo "Деплой завершен"