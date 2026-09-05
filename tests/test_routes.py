from unittest.mock import MagicMock, patch

import psycopg2


class TestIndex:
    def test_index_returns_200(self, client):
        response = client.get("/")
        assert response.status_code == 200

    def test_index_contains_form(self, client):
        response = client.get("/")
        assert b"form" in response.data
        assert b"url" in response.data


class TestUrlsList:
    def test_urls_list_returns_200(self, client, mock_db_cursor):
        mock_cursor = MagicMock()
        mock_cursor.fetchone.return_value = {"total": 0}
        mock_cursor.fetchall.return_value = []
        mock_db_cursor.return_value.__enter__ = MagicMock(
            return_value=(mock_cursor, MagicMock())
        )
        mock_db_cursor.return_value.__exit__ = MagicMock(return_value=False)

        response = client.get("/urls")
        assert response.status_code == 200

    def test_urls_list_with_pagination(self, client, mock_db_cursor):
        mock_cursor = MagicMock()
        mock_cursor.fetchone.return_value = {"total": 25}
        mock_cursor.fetchall.return_value = []
        mock_db_cursor.return_value.__enter__ = MagicMock(
            return_value=(mock_cursor, MagicMock())
        )
        mock_db_cursor.return_value.__exit__ = MagicMock(return_value=False)

        response = client.get("/urls?page=2")
        assert response.status_code == 200


class TestShowUrl:
    def test_show_url_not_found_redirects(self, client, mock_db_cursor):
        mock_cursor = MagicMock()
        mock_cursor.fetchone.return_value = None
        mock_db_cursor.return_value.__enter__ = MagicMock(
            return_value=(mock_cursor, MagicMock())
        )
        mock_db_cursor.return_value.__exit__ = MagicMock(return_value=False)

        response = client.get("/urls/999", follow_redirects=True)
        assert response.status_code == 200

    def test_show_url_found(self, client, mock_db_cursor):
        mock_cursor = MagicMock()
        mock_cursor.fetchone.return_value = {
            "id": 1,
            "name": "https://example.com",
            "created_at": None,
        }
        mock_cursor.fetchall.return_value = []
        mock_db_cursor.return_value.__enter__ = MagicMock(
            return_value=(mock_cursor, MagicMock())
        )
        mock_db_cursor.return_value.__exit__ = MagicMock(return_value=False)

        response = client.get("/urls/1")
        assert response.status_code == 200
        assert b"example.com" in response.data


class TestAddUrl:
    def test_add_url_empty_returns_422(self, client):
        response = client.post("/urls", data={"url": ""}, follow_redirects=True)
        assert response.status_code == 422

    def test_add_url_invalid_returns_422(self, client):
        response = client.post(
            "/urls",
            data={"url": "not-a-url"},
            follow_redirects=True,
        )
        assert response.status_code == 422

    def test_add_url_existing_redirects(self, client, mock_db_cursor):
        mock_cursor = MagicMock()
        mock_cursor.fetchone.return_value = {"id": 1}
        mock_db_cursor.return_value.__enter__ = MagicMock(
            return_value=(mock_cursor, MagicMock())
        )
        mock_db_cursor.return_value.__exit__ = MagicMock(return_value=False)

        response = client.post(
            "/urls",
            data={"url": "https://example.com"},
            follow_redirects=True,
        )
        assert response.status_code == 200


class TestHealthCheck:
    def test_health_ok(self, client, mock_db_cursor):
        mock_cursor = MagicMock()
        mock_db_cursor.return_value.__enter__ = MagicMock(
            return_value=(mock_cursor, MagicMock())
        )
        mock_db_cursor.return_value.__exit__ = MagicMock(return_value=False)

        response = client.get("/health")
        assert response.status_code == 200
        assert response.get_json()["status"] == "ok"

    def test_health_db_error(self, client, mock_db_cursor):
        import psycopg2

        mock_db_cursor.return_value.__enter__ = MagicMock(
            side_effect=psycopg2.Error("db down")
        )
        mock_db_cursor.return_value.__exit__ = MagicMock(return_value=False)

        response = client.get("/health")
        assert response.status_code == 503


class TestUrlsListPagination:
    def test_urls_list_page_zero_resets_to_one(self, client, mock_db_cursor):
        mock_cursor = MagicMock()
        mock_cursor.fetchone.return_value = {"total": 5}
        mock_cursor.fetchall.return_value = []
        mock_db_cursor.return_value.__enter__ = MagicMock(
            return_value=(mock_cursor, MagicMock())
        )
        mock_db_cursor.return_value.__exit__ = MagicMock(return_value=False)

        response = client.get("/urls?page=0")
        assert response.status_code == 200

    def test_urls_list_page_negative(self, client, mock_db_cursor):
        mock_cursor = MagicMock()
        mock_cursor.fetchone.return_value = {"total": 5}
        mock_cursor.fetchall.return_value = []
        mock_db_cursor.return_value.__enter__ = MagicMock(
            return_value=(mock_cursor, MagicMock())
        )
        mock_db_cursor.return_value.__exit__ = MagicMock(return_value=False)

        response = client.get("/urls?page=-1")
        assert response.status_code == 200


class TestAddUrlNew:
    def test_add_url_new_inserts_and_redirects(self, client, mock_db_cursor):
        mock_cursor = MagicMock()
        mock_cursor.fetchone.side_effect = [
            None,
            {"id": 5},
            {"id": 5, "name": "https://new-site.com", "created_at": None},
        ]
        mock_cursor.fetchall.return_value = []
        mock_conn = MagicMock()
        mock_db_cursor.return_value.__enter__ = MagicMock(
            return_value=(mock_cursor, mock_conn)
        )
        mock_db_cursor.return_value.__exit__ = MagicMock(return_value=False)

        response = client.post(
            "/urls",
            data={"url": "https://new-site.com"},
            follow_redirects=True,
        )
        assert response.status_code == 200
        mock_conn.commit.assert_called_once()


class TestCheckUrl:
    def test_check_url_not_found(self, client, mock_db_cursor):
        mock_cursor = MagicMock()
        mock_cursor.fetchone.side_effect = [
            None,
            {"total": 0},
        ]
        mock_cursor.fetchall.return_value = []
        mock_db_cursor.return_value.__enter__ = MagicMock(
            return_value=(mock_cursor, MagicMock())
        )
        mock_db_cursor.return_value.__exit__ = MagicMock(return_value=False)

        response = client.post("/urls/999/checks", follow_redirects=True)
        assert response.status_code == 200

    @patch("page_analyzer.routes.fetch_page_data")
    def test_check_url_success(self, mock_fetch, client, mock_db_cursor):
        mock_fetch.return_value = {
            "status_code": 200,
            "h1": "Test",
            "title": "Test",
            "description": "Desc",
        }
        mock_cursor = MagicMock()
        mock_cursor.fetchone.side_effect = [
            {"name": "https://example.com"},
            {"id": 1, "name": "https://example.com", "created_at": None},
        ]
        mock_cursor.fetchall.return_value = []
        mock_conn = MagicMock()
        mock_db_cursor.return_value.__enter__ = MagicMock(
            return_value=(mock_cursor, mock_conn)
        )
        mock_db_cursor.return_value.__exit__ = MagicMock(return_value=False)

        response = client.post("/urls/1/checks", follow_redirects=True)
        assert response.status_code == 200
        mock_conn.commit.assert_called_once()

    @patch("page_analyzer.routes.fetch_page_data")
    def test_check_url_network_error(self, mock_fetch, client, mock_db_cursor):
        import requests as req

        mock_fetch.side_effect = req.ConnectionError("timeout")
        mock_cursor = MagicMock()
        mock_cursor.fetchone.side_effect = [
            {"name": "https://example.com"},
            {"id": 1, "name": "https://example.com", "created_at": None},
        ]
        mock_cursor.fetchall.return_value = []
        mock_conn = MagicMock()
        mock_db_cursor.return_value.__enter__ = MagicMock(
            return_value=(mock_cursor, mock_conn)
        )
        mock_db_cursor.return_value.__exit__ = MagicMock(return_value=False)

        response = client.post("/urls/1/checks", follow_redirects=True)
        assert response.status_code == 200
        mock_conn.rollback.assert_called_once()

    @patch("page_analyzer.routes.fetch_page_data")
    def test_check_url_db_error(self, mock_fetch, client, mock_db_cursor):
        mock_fetch.return_value = {
            "status_code": 200,
            "h1": "",
            "title": "",
            "description": "",
        }
        mock_cursor = MagicMock()
        mock_cursor.fetchone.side_effect = [
            {"name": "https://example.com"},
            {"id": 1, "name": "https://example.com", "created_at": None},
        ]
        mock_cursor.fetchall.return_value = []

        call_count = 0

        def execute_side_effect(sql, params=None):
            nonlocal call_count
            call_count += 1
            if "INSERT" in sql:
                raise psycopg2.Error("db fail")

        mock_cursor.execute.side_effect = execute_side_effect
        mock_conn = MagicMock()
        mock_db_cursor.return_value.__enter__ = MagicMock(
            return_value=(mock_cursor, mock_conn)
        )
        mock_db_cursor.return_value.__exit__ = MagicMock(return_value=False)

        response = client.post("/urls/1/checks", follow_redirects=True)
        assert response.status_code == 200
        mock_conn.rollback.assert_called_once()


class TestErrorPages:
    def test_404_page(self, client):
        response = client.get("/nonexistent-page")
        assert response.status_code == 404
        assert b"404" in response.data

    def test_500_page(self, app):
        app.config["TESTING"] = False

        @app.route("/trigger-500")
        def trigger_500():
            raise RuntimeError("test error")

        with app.test_client() as c:
            response = c.get("/trigger-500")
            assert response.status_code == 500
