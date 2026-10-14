"""Kiểm thử CRUD màu không phụ thuộc GUI hay PLC."""

from __future__ import annotations

import json
import tempfile
import unittest
from pathlib import Path

from app.state import ApplicationState
from domain.color_profile import HSVRange
from repositories.color_repository import ColorRepository
from repositories.routing_repository import RoutingRepository
from services.color_management_service import ColorManagementService


class ColorManagementTests(unittest.TestCase):
    def setUp(self) -> None:
        self.temp = tempfile.TemporaryDirectory()
        root = Path(self.temp.name)
        self.color_path = root / "colors.json"
        self.color_path.write_text(
            json.dumps([
                {
                    "id": 1,
                    "key": "blue",
                    "display_name": "XANH DƯƠNG",
                    "ui_color": "#38bdf8",
                    "enabled": True,
                    "hsv_ranges": [{"lower": [90, 40, 20], "upper": [120, 255, 255]}],
                }
            ]),
            encoding="utf-8",
        )
        self.route_path = root / "routing.json"
        self.route_path.write_text(
            json.dumps([{"color_id": 1, "destination_id": 2, "enabled": True}]),
            encoding="utf-8",
        )
        self.colors = ColorRepository(self.color_path)
        self.routes = RoutingRepository(self.route_path)
        self.state = ApplicationState()
        self.manager = ColorManagementService(self.colors, self.routes, self.state)

    def tearDown(self) -> None:
        self.temp.cleanup()

    def test_add_color_disabled_and_persists(self) -> None:
        added = self.manager.create("Trắng", "#eeeeee")
        self.assertEqual(added.id, 2)
        self.assertEqual(added.key, "trang")
        self.assertFalse(added.enabled)
        self.assertIn(2, self.state.counters)
        self.assertEqual(ColorRepository(self.color_path).get(2).display_name, "Trắng")

    def test_cannot_enable_color_with_unconfigured_hsv(self) -> None:
        added = self.manager.create("Trắng", "#eeeeee")
        with self.assertRaisesRegex(ValueError, "HSV"):
            self.manager.update(added.id, "Trắng", "#eeeeee", True)

    def test_edit_color_after_hsv_configured(self) -> None:
        added = self.manager.create("Trắng", "#eeeeee")
        added.hsv_ranges = [HSVRange((0, 0, 150), (179, 40, 255))]
        self.colors.update(added)
        updated = self.manager.update(added.id, "TRẮNG SỮA", "#ffffff", True)
        self.assertEqual(updated.key, "trang")
        self.assertTrue(ColorRepository(self.color_path).get(added.id).enabled)

    def test_delete_is_blocked_while_route_exists(self) -> None:
        with self.assertRaisesRegex(ValueError, "Routing"):
            self.manager.delete(1)
        self.assertEqual(self.colors.get(1).display_name, "XANH DƯƠNG")
        self.assertIsNotNone(self.routes.get_for_color(1))

    def test_unassign_then_delete(self) -> None:
        self.routes.remove_route(1)
        self.state.ensure_color(1)
        self.manager.delete(1)
        self.assertEqual(self.colors.all(), [])
        self.assertNotIn(1, self.state.counters)
        self.assertEqual(ColorRepository(self.color_path).all(), [])

    def test_reject_duplicate_name_and_key(self) -> None:
        with self.assertRaises(ValueError):
            self.manager.create("xanh dương", "#ffffff")
        self.manager.create("Trắng", "#eeeeee")
        with self.assertRaises(ValueError):
            self.manager.create("trang", "#eeeeee")


if __name__ == "__main__":
    unittest.main()
