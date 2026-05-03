import os
import validators
import requests
from datetime import datetime
from dotenv import load_dotenv
from flask import Flask, render_template, request, redirect, url_for, flash
import psycopg2
from psycopg2.extras import RealDictCursor
from bs4 import BeautifulSoup
from urllib.parse import urlparse

# загружаем переменные окружения из .env
dotenv_path = os.path.join(os.path.dirname(__file__), "..", ".env")
load_dotenv(dotenv_path)

template_dir = os.path.abspath(
    os.path.join(os.path.dirname(__file__), "..", "templates")
)
app = Flask(__name__, template_folder=template_dir)
app.config["SECRET_KEY"] = os.getenv("SECRET_KEY", "default-secret-key-for-dev")


def get_db_connection():
    database_url = os.getenv("DATABASE_URL")
    if not database_url:
        database_url = "postgresql://localhost/page_analyzer"
    conn = psycopg2.connect(database_url, cursor_factory=RealDictCursor)
    return conn


def normalize_url(url):
    url = url.strip()
    parsed = urlparse(url)
    normalized = f"{parsed.scheme}://{parsed.netloc}"
    return normalized.lower()


def validate_url(url):
    if not url or len(url) > 255:
        return False, "URL превышает 255 символов"
    if not validators.url(url):
        return False, "Некорректный URL"
    return True, ""


def truncate_text(text, max_length=200):
    if text and len(text) > max_length:
        return text[:max_length] + "..."
    return text


@app.route("/")
def index():
    return render_template("index.html")


@app.route("/urls", methods=["GET"])
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
    return render_template("urls.html", urls=urls)


@app.route("/urls/<int:id>")
def show_url(id):
    conn = get_db_connection()
    cur = conn.cursor()
    cur.execute("SELECT id, name, created_at FROM urls WHERE id = %s", (id,))
    url = cur.fetchone()

    if not url:
        cur.close()
        conn.close()
        flash("Страница не найдена", "danger")
        return redirect(url_for("index"))

    cur.execute("""
        SELECT id, status_code, h1, title, description, created_at
        FROM url_checks
        WHERE url_id = %s
        ORDER BY created_at DESC
    """, (id,))
    checks = cur.fetchall()
    cur.close()
    conn.close()
    return render_template("show_url.html", url=url, checks=checks)


@app.route("/urls", methods=["POST"])
def add_url():
    url = request.form.get("url", "").strip()
    is_valid, error_message = validate_url(url)
    if not is_valid:
        flash(error_message, "danger")
        return render_template("index.html"), 422

    normalized_url = normalize_url(url)
    conn = get_db_connection()
    cur = conn.cursor()

    try:
        cur.execute("SELECT id FROM urls WHERE name = %s", (normalized_url,))
        existing_url = cur.fetchone()

        if existing_url:
            flash("Страница уже существует", "info")
            url_id = existing_url["id"]
        else:
            cur.execute(
                "INSERT INTO urls (name, created_at) VALUES (%s, %s) "
                "RETURNING id",
                (normalized_url, datetime.now()),
            )
            conn.commit()
            url_id = cur.fetchone()["id"]
            flash("Страница успешно добавлена", "success")

        cur.close()
        conn.close()
        return redirect(url_for("show_url", id=url_id))
    except Exception as e:
        print(f"ERROR: {e}")
        conn.rollback()
        cur.close()
        conn.close()
        flash("Ошибка при добавлении страницы", "danger")
        return render_template("index.html"), 500


@app.route("/urls/<int:id>/checks", methods=["POST"])
def check_url(id):
    conn = get_db_connection()
    cur = conn.cursor()
    cur.execute("SELECT name FROM urls WHERE id = %s", (id,))
    url_data = cur.fetchone()

    if not url_data:
        cur.close()
        conn.close()
        flash("Страница не найдена", "danger")
        return redirect(url_for("urls_list"))

    try:
        response = requests.get(url_data["name"], timeout=10)
        response.raise_for_status()

        response.encoding = response.apparent_encoding or "utf-8"
        soup = BeautifulSoup(response.text, "html.parser")

        h1 = soup.find("h1").get_text(strip=True) if soup.find("h1") else ""
        title_tag = soup.find("title")
        title = title_tag.get_text(strip=True) if title_tag else ""

        desc_tag = soup.find("meta", attrs={"name": "description"})
        description = desc_tag.get("content", "").strip() if desc_tag else ""

        h1 = truncate_text(h1, 200)
        title = truncate_text(title, 200)
        description = truncate_text(description, 200)

        cur.execute("""
            INSERT INTO url_checks 
            (url_id, status_code, h1, title, description, created_at)
            VALUES (%s, %s, %s, %s, %s, %s)
            """, (id, response.status_code, h1, title, description,
                  datetime.now()))
        conn.commit()
        flash("Страница успешно проверена", "success")
    except Exception as e:
        print(f"Check error: {e}")
        flash("Произошла ошибка при проверке", "danger")
    finally:
        cur.close()
        conn.close()

    return redirect(url_for("show_url", id=id))


if __name__ == "__main__":
    app.run(debug=True, host="0.0.0.0", port=8000)
