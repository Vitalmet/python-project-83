from unittest.mock import MagicMock


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
