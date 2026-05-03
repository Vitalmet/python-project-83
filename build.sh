#!/usr/bin/env bash

# Установка uv
curl -LsSf https://astral.sh/uv/install.sh | sh
source $HOME/.local/bin/env

# Установка зависимостей
uv sync

# Создание таблиц в базе данных
if [ -n "$DATABASE_URL" ]; then
    psql -a -d $DATABASE_URL -f database.sql
else
    echo "DATABASE_URL is not set"
    exit 1
fi