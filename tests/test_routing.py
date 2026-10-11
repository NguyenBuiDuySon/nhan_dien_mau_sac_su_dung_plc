from __future__ import annotations

import json
import tempfile
import unittest
from pathlib import Path

from repositories.color_repository import ColorRepository
from repositories.destination_repository import DestinationRepository
from repositories.routing_repository import RoutingRepository
from services.routing_service import RoutingService


class RoutingServiceTest(unittest.TestCase):
    def setUp(self) -> None:
        self.temp = tempfile.TemporaryDirectory()
        root = Path(self.temp.name)
        (root / "colors.json").write_text(
            json.dumps([
                {"id": 1, "key": "blue", "display_name": "BLUE", "ui_color": "#00aaff", "enabled": True,
                 "hsv_ranges": [{"lower": [90, 50, 50], "upper": [130, 255, 255]}]},
                {"id": 2, "key": "green", "display_name": "GREEN", "ui_color": "#00ff88", "enabled": True,
                 "hsv_ranges": [{"lower": [35, 50, 50], "upper": [85, 255, 255]}]}
            ]), encoding="utf-8"
        )
        (root / "destinations.json").write_text(
            json.dumps([{"id": 10, "key": "bin_a", "display_name": "BIN A", "x": 1, "y": 2, "z": 3, "enabled": True}]),
            encoding="utf-8"
        )
        (root / "routing.json").write_text(
            json.dumps([
                {"color_id": 1, "destination_id": 10, "enabled": True},
                {"color_id": 2, "destination_id": 10, "enabled": True}
            ]), encoding="utf-8"
        )
        colors = ColorRepository(root / "colors.json")
        destinations = DestinationRepository(root / "destinations.json")
        routes = RoutingRepository(root / "routing.json")
        self.service = RoutingService(colors, destinations, routes)

    def tearDown(self) -> None:
        self.temp.cleanup()

    def test_many_colors_can_share_one_destination(self) -> None:
        self.assertEqual(self.service.resolve(1).id, 10)
        self.assertEqual(self.service.resolve(2).id, 10)
        self.assertEqual(self.service.colors_for_destination(10), [1, 2])

    def test_configuration_is_valid(self) -> None:
        self.assertEqual(self.service.validate_configuration(), [])


if __name__ == "__main__":
    unittest.main()
