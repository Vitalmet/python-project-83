from unittest.mock import MagicMock, patch

from page_analyzer.db import get_db_connection


class TestDbConnection:
    @patch("page_analyzer.db.psycopg2.connect")
    @patch("page_analyzer.db.Config")
    def test_get_db_connection_adds_sslmode(self, mock_config, mock_connect):
        mock_config.DATABASE_URL = "postgresql://user:pass@host/db"
        mock_connect.return_value = MagicMock()

        get_db_connection()

        call_args = mock_connect.call_args[0][0]
        assert "sslmode=require" in call_args

    @patch("page_analyzer.db.psycopg2.connect")
    @patch("page_analyzer.db.Config")
    def test_get_db_connection_keeps_existing_sslmode(self, mock_config, mock_connect):
        mock_config.DATABASE_URL = "postgresql://user:pass@host/db?sslmode=prefer"
        mock_connect.return_value = MagicMock()

        get_db_connection()

        call_args = mock_connect.call_args[0][0]
        assert call_args.count("sslmode") == 1

    @patch("page_analyzer.db.psycopg2.connect")
    @patch("page_analyzer.db.Config")
    def test_get_db_connection_ampersand_separator(self, mock_config, mock_connect):
        mock_config.DATABASE_URL = "postgresql://user:pass@host/db?host=localhost"
        mock_connect.return_value = MagicMock()

        get_db_connection()

        call_args = mock_connect.call_args[0][0]
        assert "sslmode=require" in call_args
        assert "&sslmode=require" in call_args
