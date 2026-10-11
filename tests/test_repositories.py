from __future__ import annotations

import json
import tempfile
import unittest
from pathlib import Path

from domain.color_profile import ColorProfile, HSVRange
from repositories.color_repository import ColorRepository


class ColorRepositoryTest(unittest.TestCase):
    def test_add_and_disable_color(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            path = Path(temp) / "colors.json"
            path.write_text("[]", encoding="utf-8")
            repository = ColorRepository(path)
            repository.add(
                ColorProfile(
                    id=1,
                    key="blue",
                    display_name="BLUE",
                    ui_color="#38bdf8",
                    hsv_ranges=[HSVRange((90, 50, 50), (130, 255, 255))],
                )
            )
            repository.set_enabled(1, False)
            self.assertFalse(repository.get(1).enabled)
            saved = json.loads(path.read_text(encoding="utf-8"))
            self.assertEqual(saved[0]["key"], "blue")


if __name__ == "__main__":
    unittest.main()
