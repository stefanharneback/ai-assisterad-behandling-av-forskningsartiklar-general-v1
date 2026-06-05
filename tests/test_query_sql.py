from __future__ import annotations

import unittest

from article_analysis_general.query.sql import ARTICLE_REFERENCES_TABLE, shared_references_query


class SqlQueryTests(unittest.TestCase):
    def test_reference_edge_table_avoids_reserved_references_name(self) -> None:
        self.assertEqual(ARTICLE_REFERENCES_TABLE, "article_references")

    def test_shared_references_query_is_deferred_until_m4(self) -> None:
        with self.assertRaises(NotImplementedError):
            shared_references_query()


if __name__ == "__main__":
    unittest.main()
