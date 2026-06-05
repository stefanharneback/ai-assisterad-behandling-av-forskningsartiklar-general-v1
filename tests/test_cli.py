from __future__ import annotations

import io
import json
import unittest
from contextlib import redirect_stdout

from article_analysis_general.cli import main


class CliTests(unittest.TestCase):
    def test_doctor_reports_ok(self) -> None:
        buffer = io.StringIO()

        with redirect_stdout(buffer):
            exit_code = main(["doctor"])

        self.assertEqual(exit_code, 0)
        payload = json.loads(buffer.getvalue())
        self.assertEqual(payload["status"], "ok")


if __name__ == "__main__":
    unittest.main()

