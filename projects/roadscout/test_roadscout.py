import tempfile
import unittest
from datetime import date
from pathlib import Path

from roadscout import (
    DEFAULT_AVOID_TERMS,
    OfflineHotelProvider,
    SearchConfig,
    choose_best_plan,
    collect_candidates,
    generate_stop_zones,
)


class RoadScoutTests(unittest.TestCase):
    def config(self) -> SearchConfig:
        temp = Path(tempfile.mkdtemp())
        return SearchConfig(
            origin="Bethlehem, PA",
            destination="Las Vegas, NV",
            route="southern-i40",
            nights=4,
            checkin_date=date(2026, 5, 27),
            adults=1,
            max_nightly=85,
            budget=800,
            mpg=25,
            fuel_price=3.55,
            search_radius=20,
            avoid_terms=DEFAULT_AVOID_TERMS,
            output_dir=temp,
            cache_path=temp / "cache.sqlite3",
            live_prices=False,
            live_places=False,
            live_route=False,
            live_hotelbeds=False,
            hotelbeds_env="test",
            hotelbeds_auto_destinations=False,
        )

    def test_generates_expected_stop_zones(self) -> None:
        zones = generate_stop_zones(self.config())
        self.assertEqual(len(zones), 12)
        self.assertEqual(zones[0].town, "Wytheville, VA")
        self.assertEqual(zones[-1].town, "Holbrook, AZ")

    def test_collects_and_rejects_bad_seed_options(self) -> None:
        accepted, rejected = collect_candidates(self.config(), [OfflineHotelProvider()])
        self.assertGreater(len(accepted), 20)
        self.assertTrue(any(row.rejected_reason for row in rejected))
        self.assertTrue(all(row.rating >= 3.2 for row in accepted))

    def test_best_plan_has_one_hotel_per_night(self) -> None:
        config = self.config()
        accepted, _ = collect_candidates(config, [OfflineHotelProvider()])
        plan = choose_best_plan(accepted, config)
        self.assertEqual(len(plan.hotels), 4)
        self.assertLess(plan.hotel_total, config.budget)
        self.assertEqual([hotel.night for hotel in plan.hotels], [1, 2, 3, 4])


if __name__ == "__main__":
    unittest.main()
