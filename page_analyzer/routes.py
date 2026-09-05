import logging

import psycopg2
import requests
from flask import Blueprint, flash, jsonify, redirect, render_template, request, url_for

from page_analyzer.db import db_cursor
from page_analyzer.extensions import limiter
from page_analyzer.services import fetch_page_data, normalize_url, validate_url

logger = logging.getLogger(__name__)

bp = Blueprint("main", __name__)

ITEMS_PER_PAGE = 10


@bp.route("/")
def index() -> str:
    return render_template("index.html")


@bp.route("/urls", methods=["GET"])
def urls_list() -> str:
    page = request.args.get("page", 1, type=int)
    if page < 1:
        page = 1
    offset = (page - 1) * ITEMS_PER_PAGE

    with db_cursor() as (cur, _):
        cur.execute(
            """
            SELECT COUNT(*) as total FROM urls
            """
        )
        total = cur.fetchone()["total"]
        total_pages = max(1, -(-total // ITEMS_PER_PAGE))

        cur.execute(
            """
            SELECT
                u.id,
                u.name,
                u.created_at,
                lc.last_check_at,
                lc.status_code
            FROM urls u
            LEFT JOIN LATERAL (
                SELECT
                    created_at as last_check_at,
                    status_code
                FROM url_checks
                WHERE url_id = u.id
                ORDER BY created_at DESC
                LIMIT 1
            ) lc ON true
            ORDER BY u.created_at DESC
            LIMIT %s OFFSET %s
            """,
            (ITEMS_PER_PAGE, offset),
        )
        urls = cur.fetchall()

    return render_template(
        "urls.html",
        urls=urls,
        page=page,
        total_pages=total_pages,
    )


@bp.route("/urls/<int:url_id>")
def show_url(url_id: int) -> str:
    with db_cursor() as (cur, _):
        cur.execute("SELECT id, name, created_at FROM urls WHERE id = %s", (url_id,))
        url = cur.fetchone()

        if not url:
            flash("Страница не найдена", "danger")
            return redirect(url_for("main.index"))

        cur.execute(
            """
            SELECT id, status_code, h1, title, description, created_at
            FROM url_checks
            WHERE url_id = %s
            ORDER BY created_at DESC
            """,
            (url_id,),
        )
        checks = cur.fetchall()
    return render_template("show_url.html", url=url, checks=checks)


@bp.route("/urls", methods=["POST"])
def add_url() -> str:
    url = request.form.get("url", "").strip()
    is_valid, error_message = validate_url(url)
    if not is_valid:
        flash(error_message, "danger")
        return render_template("index.html"), 422

    normalized_url = normalize_url(url)

    with db_cursor() as (cur, conn):
        cur.execute("SELECT id FROM urls WHERE name = %s", (normalized_url,))
        existing_url = cur.fetchone()

        if existing_url:
            flash("Страница уже существует", "info")
            url_id = existing_url["id"]
        else:
            cur.execute(
                "INSERT INTO urls (name, created_at) VALUES (%s, NOW()) RETURNING id",
                (normalized_url,),
            )
            conn.commit()
            url_id = cur.fetchone()["id"]
            flash("Страница успешно добавлена", "success")

    return redirect(url_for("main.show_url", url_id=url_id))


@bp.route("/urls/<int:url_id>/checks", methods=["POST"])
@limiter.limit("5 per minute")
def check_url(url_id: int) -> str:
    with db_cursor() as (cur, conn):
        cur.execute("SELECT name FROM urls WHERE id = %s", (url_id,))
        url_data = cur.fetchone()

        if not url_data:
            flash("Страница не найдена", "danger")
            return redirect(url_for("main.urls_list"))

        try:
            page_data = fetch_page_data(url_data["name"])
            cur.execute(
                """
                INSERT INTO url_checks
                (url_id, status_code, h1, title, description, created_at)
                VALUES (%s, %s, %s, %s, %s, NOW())
                """,
                (
                    url_id,
                    page_data["status_code"],
                    page_data["h1"],
                    page_data["title"],
                    page_data["description"],
                ),
            )
            conn.commit()
            flash("Страница успешно проверена", "success")
        except requests.RequestException as e:
            logger.warning("Network error checking url %d: %s", url_id, e)
            conn.rollback()
            flash("Не удалось подключиться к сайту", "danger")
        except psycopg2.Error as e:
            logger.error("Database error checking url %d: %s", url_id, e)
            conn.rollback()
            flash("Ошибка базы данных при проверке", "danger")

    return redirect(url_for("main.show_url", url_id=url_id))


@bp.route("/health")
def health_check() -> tuple:
    try:
        with db_cursor() as (cur, _):
            cur.execute("SELECT 1")
        return jsonify({"status": "ok"}), 200
    except psycopg2.Error:
        logger.error("Health check failed: database unreachable")
        return jsonify({"status": "error", "message": "Database unavailable"}), 503
