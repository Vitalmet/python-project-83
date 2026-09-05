from unittest.mock import MagicMock, patch

from page_analyzer.app import SCHEMA_SQL, init_db


class TestInitDb:
    @patch("page_analyzer.app.get_db_connection")
    def test_init_db_creates_tables(self, mock_get_conn):
        mock_conn = MagicMock()
        mock_get_conn.return_value = mock_conn

        init_db()

        mock_conn.cursor.assert_called_once()
        mock_conn.commit.assert_called_once()
        mock_conn.close.assert_called_once()
        mock_conn.cursor().__enter__().execute.assert_called_once_with(SCHEMA_SQL)

    @patch("page_analyzer.app.get_db_connection")
    def test_init_db_handles_connection_error(self, mock_get_conn):
        mock_get_conn.side_effect = Exception("Connection refused")

        init_db()

        mock_get_conn.assert_called_once()

    @patch("page_analyzer.app.get_db_connection")
    def test_init_db_handles_commit_error(self, mock_get_conn):
        mock_conn = MagicMock()
        mock_conn.commit.side_effect = Exception("Commit failed")
        mock_get_conn.return_value = mock_conn

        init_db()

        mock_get_conn.assert_called_once()
