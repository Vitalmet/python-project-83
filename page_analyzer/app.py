import os
import traceback

from flask import Flask, Response, render_template
from flask_wtf.csrf import CSRFProtect

from page_analyzer.config import Config
from page_analyzer.db import get_db_connection
from page_analyzer.extensions import limiter
from page_analyzer.routes import bp

template_dir = os.path.abspath(
    os.path.join(os.path.dirname(__file__), '..', 'templates')
)

csrf = CSRFProtect()

SCHEMA_SQL = """
CREATE TABLE IF NOT EXISTS urls (
    id SERIAL PRIMARY KEY,
    name VARCHAR(255) NOT NULL UNIQUE,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS url_checks (
    id SERIAL PRIMARY KEY,
    url_id INTEGER REFERENCES urls(id) ON DELETE CASCADE,
    status_code INTEGER,
    h1 TEXT,
    title TEXT,
    description TEXT,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX IF NOT EXISTS idx_urls_name ON urls (name);
CREATE INDEX IF NOT EXISTS idx_urls_created_at ON urls (created_at DESC);
CREATE INDEX IF NOT EXISTS idx_checks_url_id_created ON url_checks (url_id, created_at DESC);
"""


def init_db() -> None:
    try:
        conn = get_db_connection()
        with conn.cursor() as cur:
            cur.execute(SCHEMA_SQL)
        conn.commit()
        print("Database tables initialized", flush=True)
        conn.close()
    except Exception as e:
        print(f"Database init error: {e}", flush=True)


def create_app() -> Flask:
    app = Flask(__name__, template_folder=template_dir)
    app.config.from_object(Config)

    csrf.init_app(app)
    limiter.init_app(app)

    init_db()

    app.register_blueprint(bp)

    @app.after_request
    def set_security_headers(response: Response) -> Response:
        response.headers['X-Content-Type-Options'] = 'nosniff'
        response.headers['X-Frame-Options'] = 'DENY'
        response.headers['X-XSS-Protection'] = '1; mode=block'
        response.headers['Referrer-Policy'] = 'strict-origin-when-cross-origin'
        return response

    @app.errorhandler(404)
    def not_found(error: Exception) -> tuple[str, int]:
        return render_template('404.html'), 404

    @app.errorhandler(500)
    def internal_error(error: Exception) -> tuple[str, int]:
        print('=== 500 ERROR ===', flush=True)
        traceback.print_exc()
        return render_template('500.html'), 500

    return app


app = create_app()

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=8000)
