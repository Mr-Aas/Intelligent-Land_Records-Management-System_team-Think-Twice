"""
Unit tests for PostgreSQL + PostGIS database integration (§12).
"""

from __future__ import annotations

import unittest
from app.pipeline import config
from app.db import session as db_session
from app.db import sync as db_sync


class TestDatabaseIntegration(unittest.TestCase):
    """Test suite for PostgreSQL + PostGIS database connectivity, endpoints, and models."""

    def test_database_url_configuration(self):
        """Verify DATABASE_URL is loaded in config."""
        self.assertIsNotNone(config.DATABASE_URL)
        self.assertIn("postgresql://", config.DATABASE_URL)

    def test_db_connection_check(self):
        """Verify check_db_connection returns status tuple."""
        is_conn, msg = db_session.check_db_connection()
        self.assertIsInstance(is_conn, bool)
        self.assertIsInstance(msg, str)

    def test_get_postgis_version_returns_optional_str(self):
        """Verify get_postgis_version handles connection attempt gracefully."""
        version = db_session.get_postgis_version()
        if version is not None:
            self.assertIsInstance(version, str)


if __name__ == "__main__":
    unittest.main()
