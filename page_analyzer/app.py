import os
import validators
import requests
from datetime import datetime
from dotenv import load_dotenv
from flask import Flask, render_template, request, redirect, url_for, flash
import psycopg2
from psycopg2.extras import RealDictCursor
from bs4 import BeautifulSoup

#загружаем переменные окружения из .env
dotenv_path = os.path.join(os.path.dirname(__file__), '..', '.env')
load_dotenv(dotenv_path)

template_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', 'templates'))
app = Flask(__name__, template_folder=template_dir)
app.config['SECRET_KEY'] = os.getenv('SECRET_KEY', 'default-secret-key-for-dev')

# CLEAR CACHE - force rebuild 2026-05-03 09:45
# функция для соединения с БД
def get_db_connection():
    database_url = os.getenv('DATABASE_URL')
    if not database_url:
        database_url = 'postgresql://localhost/page_analyzer'
    conn = psycopg2.connect(database_url, cursor_factory=RealDictCursor)
    return conn

# нормализация URL (удаление trailing slash и приведение к нижнему регистру)
def normalize_url(url):

    url = url.strip()
    while url.endswith('/'):
        url = url[:-1]
    url = url.lower()
    return url


# Валидация URL
def validate_url(url):
    if not url or len(url) > 255:
        return False, 'URL превышает 255 символов'
    if not validators.url(url):
        return False, 'Некорректный URL'
    return True, ''

# Функция для усечения длинного текста
def truncate_text(text, max_length=200):
    if text and len(text) > max_length:
        return text[:max_length] + '...'
    return text

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/urls', methods=['GET'])
def urls_list():
    conn = get_db_connection()
    cur = conn.cursor()

    cur.execute("""
        SELECT 
            u.id,
            u.name,
            u.created_at,
            MAX(uc.created_at) as last_check_at,
            (SELECT status_code FROM url_checks 
             WHERE url_id = u.id 
             ORDER BY created_at DESC LIMIT 1) as status_code
        FROM urls u
        LEFT JOIN url_checks uc ON u.id = uc.url_id
        GROUP BY u.id
        ORDER BY u.created_at DESC
    """)
    urls = cur.fetchall()

    cur.close()
    conn.close()

    return render_template('urls.html', urls=urls)

@app.route('/urls/<int:id>')
def show_url(id):
    conn = get_db_connection()
    cur = conn.cursor()

    cur.execute('SELECT id, name, created_at FROM urls WHERE id = %s', (id,))
    url = cur.fetchone()

    if not url:
        cur.close()
        conn.close()
        flash('Страница не найдена', 'danger')
        return redirect(url_for('index'))

    cur.execute("""
        SELECT id, status_code, h1, title, description, created_at
        FROM url_checks  -- Исправлено: urls_checks -> url_checks
        WHERE url_id = %s
        ORDER BY created_at DESC
    """, (id,))
    checks = cur.fetchall()
    cur.close()
    conn.close()

    return render_template('show_url.html', url=url, checks=checks)


@app.route('/urls', methods=['POST'])
def add_url():
    url = request.form.get('url', '').strip()

    is_valid, error_message = validate_url(url)
    if not is_valid:
        flash(error_message, 'danger')
        return render_template('index.html'), 422

    # Нормализация: только нижний регистр
    normalized_url = url.lower().rstrip('/')

    conn = get_db_connection()
    cur = conn.cursor()

    try:
        # Диагностика: посмотрим, что есть в базе
        cur.execute('SELECT id FROM urls WHERE name = %s', (normalized_url,))
        existing_url = cur.fetchone()

        if existing_url:
            flash('Страница уже существует', 'warning')
            url_id = existing_url['id']
        else:
            cur.execute('INSERT INTO urls (name, created_at) VALUES (%s, %s) RETURNING id',
                        (normalized_url, datetime.now()))
            conn.commit()
            result = cur.fetchone()
            url_id = result['id']
            flash('Страница успешно добавлена', 'success')

        cur.close()
        conn.close()
        return redirect(url_for('show_url', id=url_id))

    except Exception as e:
        conn.rollback()
        cur.close()
        conn.close()
        flash('Ошибка при добавлении страницы', 'danger')
        return render_template('index.html'), 500


@app.route('/urls/<int:id>/checks', methods=['POST'])
def check_url(id):
    conn = get_db_connection()
    cur = conn.cursor()

    cur.execute('SELECT name FROM urls WHERE id = %s', (id,))
    url_data = cur.fetchone()

    if not url_data:
        cur.close()
        conn.close()
        flash('Страница не найдена', 'danger')
        return redirect(url_for('urls_list'))

    url = url_data['name']

    try:
        response = requests.get(url, timeout=10)

        # Проверка на успешный ответ (код 200-399)
        if response.status_code >= 400:
            flash('Произошла ошибка при проверке', 'danger')
            return redirect(url_for('show_url', id=id))

        # Определяем кодировку
        response.encoding = response.apparent_encoding or 'utf-8'

        soup = BeautifulSoup(response.text, 'html.parser')

        # Извлекаем данные
        h1 = soup.find('h1').get_text(strip=True) if soup.find('h1') else ''
        title = soup.find('title').get_text(strip=True) if soup.find('title') else ''
        description_tag = soup.find('meta', attrs={'name': 'description'})
        description = description_tag.get('content', '').strip() if description_tag else ''

        # Сохраняем проверку
        cur.execute("""
            INSERT INTO url_checks (url_id, status_code, h1, title, description, created_at)
            VALUES (%s, %s, %s, %s, %s, %s)
        """, (id, response.status_code, h1, title, description, datetime.now()))

        conn.commit()
        flash('Страница успешно проверена', 'success')

    except requests.exceptions.RequestException:
        flash('Произошла ошибка при проверке', 'danger')
    finally:
        cur.close()
        conn.close()

    return redirect(url_for('show_url', id=id))

if __name__ == "__main__":
    app.run(debug=True, host='0.0.0.0', port=8000)