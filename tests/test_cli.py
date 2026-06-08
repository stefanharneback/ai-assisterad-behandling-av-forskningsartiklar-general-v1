from __future__ import annotations

import io
import json
import tempfile
import unittest
from contextlib import redirect_stdout
from pathlib import Path

import fitz  # PyMuPDF

from article_analysis_general.cli import main


class CliTests(unittest.TestCase):
    def test_doctor_reports_ok(self) -> None:
        buffer = io.StringIO()

        with redirect_stdout(buffer):
            exit_code = main(["doctor"])

        self.assertEqual(exit_code, 0)
        payload = json.loads(buffer.getvalue())
        self.assertEqual(payload["status"], "ok")

    def test_ingest_writes_run_folder_and_prints_summary(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            corpus = root / "Forskning"
            (corpus / "SCOPUS").mkdir(parents=True)
            document = fitz.open()
            document.new_page().insert_text((72, 72), "Abstract, method and results section text.")
            document.save(str(corpus / "SCOPUS" / "paper.pdf"))
            document.close()
            out = root / "runs"

            buffer = io.StringIO()
            with redirect_stdout(buffer):
                exit_code = main(["ingest", "--corpus", str(corpus), "--out", str(out)])

            self.assertEqual(exit_code, 0)
            summary = json.loads(buffer.getvalue())
            self.assertEqual(summary["article_count"], 1)
            run_dir = Path(summary["run_dir"])
            self.assertTrue((run_dir / "manifest.json").exists())
            self.assertEqual(len(list((run_dir / "records").glob("*.json"))), 1)


if __name__ == "__main__":
    unittest.main()

