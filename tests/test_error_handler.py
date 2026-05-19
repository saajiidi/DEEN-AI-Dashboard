import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from FrontEnd.utils.error_handler import log_error, get_logs, ERROR_LOG_FILE


class TestErrorHandler(unittest.TestCase):
    def test_log_error_persists_prompt_and_metadata(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            root = Path(tmpdir)
            error_file = root / "error_logs.json"
            prompt_dir = root / "error_prompts"
            prompt_dir.mkdir()
            latest_prompt = prompt_dir / "latest_error_prompt.md"

            with (
                patch("FrontEnd.utils.error_handler.DATA_DIR", root),
                patch("FrontEnd.utils.error_handler.ERROR_LOG_FILE", error_file),
                patch("FrontEnd.utils.error_handler.PROMPT_DIR", prompt_dir),
                patch("FrontEnd.utils.error_handler.LATEST_PROMPT_FILE", latest_prompt),
            ):
                entry = log_error(ValueError("boom"), context="Unit Test", details={"step": "load"})

            self.assertIsNotNone(entry)
            self.assertTrue(error_file.exists())
            self.assertTrue(latest_prompt.exists())
            self.assertIn("SYSTEM ERROR DETECTED FOR FIXING", latest_prompt.read_text(encoding="utf-8"))
            logs = get_logs() if ERROR_LOG_FILE == error_file else []
            if not logs:
                import json
                logs = json.loads(error_file.read_text(encoding="utf-8"))
            self.assertEqual(logs[-1]["context"], "Unit Test")
            self.assertEqual(logs[-1]["error_type"], "ValueError")


if __name__ == "__main__":
    unittest.main()
