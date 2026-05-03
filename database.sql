-- Очистка таблиц перед тестами
DROP TABLE IF EXISTS url_checks CASCADE;
DROP TABLE IF EXISTS urls CASCADE;

-- Создание таблицы urls
CREATE TABLE urls (
    id SERIAL PRIMARY KEY,
    name VARCHAR(255) NOT NULL UNIQUE,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- Создание таблицы checks (проверки)
CREATE TABLE url_checks (
    id SERIAL PRIMARY KEY,
    url_id INTEGER REFERENCES urls(id) ON DELETE CASCADE,
    status_code INTEGER,
    h1 TEXT,
    title TEXT,
    description TEXT,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- Создание индексов
CREATE INDEX idx_urls_name ON urls (name);
CREATE INDEX idx_checks_url_id ON url_checks (url_id);
CREATE INDEX idx_checks_created_at ON url_checks (created_at DESC);