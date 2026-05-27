#!/usr/bin/env python3
"""
RoadScout: budget route lodging scanner.

This is intentionally a route hotel scanner, not a generic hotel search engine.
It generates stop zones for a known road-trip corridor, finds lodging candidates,
scores them by road-trip usefulness, and emits CLI, CSV, HTML, and JSON reports.
"""

from __future__ import annotations

import argparse
import csv
import hashlib
import html
import json
import math
import os
import sqlite3
import sys
import textwrap
import time
import urllib.error
import urllib.parse
import urllib.request
from dataclasses import asdict, dataclass
from datetime import UTC, date, datetime, timedelta
from pathlib import Path
from typing import Iterable


DEFAULT_AVOID_TERMS = [
    "downtown Nashville",
    "Memphis",
    "OKC",
    "Albuquerque",
    "Flagstaff",
]

BAD_REVIEW_TERMS = [
    "bugs",
    "bed bugs",
    "break-in",
    "break in",
    "unsafe",
    "dirty sheets",
    "stolen",
    "roaches",
]

ROUTE_PROFILES = {
    "southern-i40": [
        {
            "night": 1,
            "towns": ["Wytheville, VA", "Bristol, TN", "Kingsport, TN"],
            "target_mile": 520,
        },
        {
            "night": 2,
            "towns": ["Dickson, TN", "Jackson, TN", "Brownsville, TN"],
            "target_mile": 920,
        },
        {
            "night": 3,
            "towns": ["Weatherford, OK", "Clinton, OK", "Elk City, OK"],
            "target_mile": 1420,
        },
        {
            "night": 4,
            "towns": ["Grants, NM", "Gallup, NM", "Holbrook, AZ"],
            "target_mile": 1900,
        },
    ]
}

TOWN_MILES = {
    "Bethlehem, PA": 0,
    "Wytheville, VA": 512,
    "Bristol, TN": 594,
    "Kingsport, TN": 616,
    "Dickson, TN": 848,
    "Jackson, TN": 935,
    "Brownsville, TN": 963,
    "Weatherford, OK": 1387,
    "Clinton, OK": 1404,
    "Elk City, OK": 1433,
    "Grants, NM": 1845,
    "Gallup, NM": 1908,
    "Holbrook, AZ": 2003,
    "Las Vegas, NV": 2360,
}


@dataclass(frozen=True)
class SearchConfig:
    origin: str
    destination: str
    route: str
    nights: int
    checkin_date: date
    adults: int
    max_nightly: float
    budget: float
    mpg: float
    fuel_price: float
    search_radius: float
    avoid_terms: list[str]
    output_dir: Path
    cache_path: Path
    live_prices: bool
    live_places: bool
    live_route: bool
    live_hotelbeds: bool
    hotelbeds_env: str
    hotelbeds_auto_destinations: bool


@dataclass(frozen=True)
class StopZone:
    night: int
    town: str
    target_mile: int


@dataclass
class HotelCandidate:
    night: int
    town: str
    name: str
    price: float
    rating: float
    reviews: int
    detour_miles: float
    detour_minutes: float
    free_cancellation: bool
    parking: bool
    address: str
    link: str
    source: str
    review_snippet: str = ""
    score: float = 0.0
    rejected_reason: str = ""


@dataclass(frozen=True)
class TripPlan:
    hotels: list[HotelCandidate]
    hotel_total: float
    fuel_estimate: float
    detour_fuel_cost: float
    remaining_budget: float
    total_score: float
    daily_miles: list[float]


class Cache:
    def __init__(self, path: Path) -> None:
        self.path = path
        self.path.parent.mkdir(parents=True, exist_ok=True)
        self.conn = sqlite3.connect(path)
        self.conn.execute(
            """
            CREATE TABLE IF NOT EXISTS hotel_searches (
                cache_key TEXT PRIMARY KEY,
                created_at TEXT NOT NULL,
                payload TEXT NOT NULL
            )
            """
        )
        self.conn.commit()

    def get(self, key: str) -> list[dict] | None:
        row = self.conn.execute(
            "SELECT payload FROM hotel_searches WHERE cache_key = ?", (key,)
        ).fetchone()
        if not row:
            return None
        return json.loads(row[0])

    def set(self, key: str, payload: list[dict]) -> None:
        self.conn.execute(
            """
            INSERT OR REPLACE INTO hotel_searches(cache_key, created_at, payload)
            VALUES (?, ?, ?)
            """,
            (key, datetime.now(UTC).isoformat(timespec="seconds"), json.dumps(payload)),
        )
        self.conn.commit()


class HotelProvider:
    def search(self, town: str, night: int, checkin: date, checkout: date, config: SearchConfig) -> list[HotelCandidate]:
        raise NotImplementedError


class OfflineHotelProvider(HotelProvider):
    """Deterministic seed data shaped like roadside Google Hotels results."""

    SEED_DATA = {
        "Wytheville, VA": [
            ("Days Inn by Wyndham Wytheville", 64, 3.7, 1040, 0.8, True, True),
            ("Super 8 by Wyndham Wytheville", 69, 3.8, 910, 1.1, True, True),
            ("Red Roof Inn Wytheville", 76, 4.0, 1220, 1.4, True, True),
            ("Budget Host Inn Wytheville", 54, 3.1, 88, 0.6, False, True),
        ],
        "Bristol, TN": [
            ("Motel 6 Bristol TN", 68, 3.6, 680, 2.6, True, True),
            ("Quality Inn Bristol", 82, 3.9, 740, 2.1, True, True),
            ("Red Roof Inn Bristol", 79, 3.8, 830, 1.7, True, True),
        ],
        "Kingsport, TN": [
            ("Super 8 by Wyndham Kingsport", 73, 3.5, 560, 5.2, True, True),
            ("Red Roof Inn Kingsport", 81, 3.8, 780, 4.9, True, True),
            ("Motel 6 Kingsport", 70, 3.4, 410, 5.5, False, True),
        ],
        "Dickson, TN": [
            ("Motel 6 Dickson TN", 62, 3.6, 600, 1.3, True, True),
            ("Super 8 by Wyndham Dickson", 72, 3.7, 720, 1.1, True, True),
            ("Econo Lodge Inn and Suites Dickson", 75, 3.8, 690, 1.7, True, True),
        ],
        "Jackson, TN": [
            ("Red Roof Inn and Suites Jackson TN", 68, 3.9, 1180, 1.2, True, True),
            ("Super 8 by Wyndham Jackson", 63, 3.6, 820, 0.9, True, True),
            ("Motel 6 Jackson TN", 61, 3.4, 710, 1.4, False, True),
        ],
        "Brownsville, TN": [
            ("Days Inn by Wyndham Brownsville", 67, 3.7, 430, 2.8, True, True),
            ("Econo Lodge Brownsville", 72, 3.6, 360, 2.2, True, True),
            ("OYO Hotel Brownsville TN", 55, 3.0, 130, 1.9, False, True),
        ],
        "Weatherford, OK": [
            ("Scottish Inns Weatherford", 59, 3.6, 460, 0.7, True, True),
            ("Travel Inn Weatherford", 62, 3.4, 220, 1.0, False, True),
            ("Best Western Plus Weatherford", 94, 4.3, 980, 1.5, True, True),
        ],
        "Clinton, OK": [
            ("Super 8 by Wyndham Clinton", 57, 3.7, 610, 0.4, True, True),
            ("Motel 6 Clinton OK", 55, 3.6, 520, 0.6, False, True),
            ("Days Inn by Wyndham Clinton", 68, 3.8, 740, 0.9, True, True),
        ],
        "Elk City, OK": [
            ("Motel 6 Elk City OK", 58, 3.5, 530, 0.8, False, True),
            ("Super 8 by Wyndham Elk City", 66, 3.8, 690, 1.2, True, True),
            ("Americas Best Value Inn Elk City", 61, 3.7, 480, 0.9, True, True),
        ],
        "Grants, NM": [
            ("Motel 6 Grants NM", 55, 3.6, 900, 0.8, False, True),
            ("Super 8 by Wyndham Grants", 62, 3.7, 680, 0.7, True, True),
            ("Days Inn by Wyndham Grants", 69, 3.8, 760, 1.3, True, True),
        ],
        "Gallup, NM": [
            ("Motel 6 Gallup", 58, 3.5, 840, 1.0, False, True),
            ("Super 8 by Wyndham Gallup", 64, 3.7, 790, 1.5, True, True),
            ("Red Roof Inn Gallup", 72, 3.9, 920, 1.8, True, True),
        ],
        "Holbrook, AZ": [
            ("Motel 6 Holbrook AZ", 59, 3.6, 640, 1.2, False, True),
            ("Super 8 by Wyndham Holbrook", 71, 3.8, 720, 1.4, True, True),
            ("Econo Lodge Holbrook", 76, 3.9, 690, 1.0, True, True),
        ],
    }

    def search(self, town: str, night: int, checkin: date, checkout: date, config: SearchConfig) -> list[HotelCandidate]:
        rows = self.SEED_DATA.get(town, [])
        candidates = []
        for name, price, rating, reviews, detour, cancel, parking in rows:
            candidates.append(
                HotelCandidate(
                    night=night,
                    town=town,
                    name=name,
                    price=float(price),
                    rating=float(rating),
                    reviews=int(reviews),
                    detour_miles=float(detour),
                    detour_minutes=round(float(detour) * 2.5 + 3, 1),
                    free_cancellation=bool(cancel),
                    parking=bool(parking),
                    address=town,
                    link=maps_search_url(name, town),
                    source="offline-seed",
                    review_snippet="Roadside budget property; cross-check recent reviews before booking.",
                )
            )
        return candidates


class SerpApiGoogleHotelsProvider(HotelProvider):
    def __init__(self, cache: Cache) -> None:
        self.cache = cache
        self.api_key = os.environ.get("SERPAPI_API_KEY")

    def available(self) -> bool:
        return bool(self.api_key)

    def search(self, town: str, night: int, checkin: date, checkout: date, config: SearchConfig) -> list[HotelCandidate]:
        if not self.api_key:
            return []
        key = f"serpapi:{town}:{checkin.isoformat()}:{checkout.isoformat()}:{config.adults}"
        cached = self.cache.get(key)
        if cached is None:
            cached = self._fetch(town, checkin, checkout, config)
            self.cache.set(key, cached)
        return [self._candidate_from_serpapi(row, town, night) for row in cached]

    def _fetch(self, town: str, checkin: date, checkout: date, config: SearchConfig) -> list[dict]:
        params = {
            "engine": "google_hotels",
            "q": f"cheap hotels in {town}",
            "check_in_date": checkin.isoformat(),
            "check_out_date": checkout.isoformat(),
            "adults": str(config.adults),
            "currency": "USD",
            "gl": "us",
            "hl": "en",
            "api_key": self.api_key or "",
        }
        url = "https://serpapi.com/search.json?" + urllib.parse.urlencode(params)
        with urllib.request.urlopen(url, timeout=30) as response:
            payload = json.loads(response.read().decode("utf-8"))
        return payload.get("properties", [])[:20]

    def _candidate_from_serpapi(self, row: dict, town: str, night: int) -> HotelCandidate:
        rate = row.get("rate_per_night") or {}
        price = parse_price(rate.get("lowest") or rate.get("extracted_lowest") or row.get("price"))
        gps = row.get("gps_coordinates") or {}
        name = str(row.get("name") or "Unnamed hotel")
        detour = float(row.get("distance") or 3.0) if isinstance(row.get("distance"), (int, float)) else 3.0
        return HotelCandidate(
            night=night,
            town=town,
            name=name,
            price=price or 9999,
            rating=float(row.get("overall_rating") or row.get("rating") or 0),
            reviews=int(row.get("reviews") or row.get("reviews_count") or 0),
            detour_miles=detour,
            detour_minutes=round(detour * 2.5 + 3, 1),
            free_cancellation="free cancellation" in json.dumps(row).lower(),
            parking="parking" in json.dumps(row).lower(),
            address=str(row.get("address") or town),
            link=str(row.get("link") or maps_search_url(name, town)),
            source="serpapi-google-hotels",
            review_snippet=str(row.get("description") or ""),
        )


class GooglePlacesTextSearchProvider(HotelProvider):
    """Places candidate discovery. Google Places does not reliably include prices."""

    def __init__(self, cache: Cache) -> None:
        self.cache = cache
        self.api_key = os.environ.get("GOOGLE_MAPS_API_KEY") or os.environ.get("GOOGLE_PLACES_API_KEY")

    def available(self) -> bool:
        return bool(self.api_key)

    def search(self, town: str, night: int, checkin: date, checkout: date, config: SearchConfig) -> list[HotelCandidate]:
        if not self.api_key:
            return []
        key = f"google-places:{town}:{config.search_radius}:{config.adults}"
        cached = self.cache.get(key)
        if cached is None:
            cached = self._fetch(town, config)
            self.cache.set(key, cached)
        return [self._candidate_from_place(row, town, night, config) for row in cached]

    def _fetch(self, town: str, config: SearchConfig) -> list[dict]:
        url = "https://places.googleapis.com/v1/places:searchText"
        body = json.dumps(
            {
                "textQuery": f"cheap motels hotels near interstate {town}",
                "maxResultCount": 20,
                "includedType": "lodging",
                "rankPreference": "RELEVANCE",
            }
        ).encode("utf-8")
        headers = {
            "Content-Type": "application/json",
            "X-Goog-Api-Key": self.api_key or "",
            "X-Goog-FieldMask": ",".join(
                [
                    "places.displayName",
                    "places.formattedAddress",
                    "places.googleMapsUri",
                    "places.location",
                    "places.rating",
                    "places.userRatingCount",
                ]
            ),
        }
        request = urllib.request.Request(url, data=body, headers=headers, method="POST")
        with urllib.request.urlopen(request, timeout=30) as response:
            payload = json.loads(response.read().decode("utf-8"))
        return payload.get("places", [])

    def _candidate_from_place(self, row: dict, town: str, night: int, config: SearchConfig) -> HotelCandidate:
        display = row.get("displayName") or {}
        name = str(display.get("text") or "Unnamed lodging")
        detour = 3.0
        return HotelCandidate(
            night=night,
            town=town,
            name=name,
            price=float(config.max_nightly),
            rating=float(row.get("rating") or 0),
            reviews=int(row.get("userRatingCount") or 0),
            detour_miles=detour,
            detour_minutes=round(detour * 2.5 + 3, 1),
            free_cancellation=False,
            parking=False,
            address=str(row.get("formattedAddress") or town),
            link=str(row.get("googleMapsUri") or maps_search_url(name, town)),
            source="google-places",
            review_snippet="Price unknown from Google Places; pair with SerpAPI/booking-site price check.",
        )


class HotelbedsAvailabilityProvider(HotelProvider):
    """Hotelbeds availability backup.

    Hotelbeds needs destination or hotel codes, so this provider is opt-in and
    uses HOTELBEDS_DESTINATION_CODES_JSON to map RoadScout towns to Hotelbeds
    destination codes when you have them.
    """

    def __init__(self, cache: Cache, environment: str) -> None:
        self.cache = cache
        self.environment = environment
        self.api_key = os.environ.get("HOTELBEDS_API_KEY")
        self.secret = os.environ.get("HOTELBEDS_SECRET")
        self.destination_codes = load_hotelbeds_destination_codes()

    def available(self) -> bool:
        return bool(self.api_key and self.secret)

    def missing_reason(self) -> str:
        if not self.api_key:
            return "HOTELBEDS_API_KEY is missing"
        if not self.secret:
            return "HOTELBEDS_SECRET is missing"
        return ""

    def search(self, town: str, night: int, checkin: date, checkout: date, config: SearchConfig) -> list[HotelCandidate]:
        if not self.available():
            return []
        destination_code = self.destination_codes.get(town)
        if not destination_code and config.hotelbeds_auto_destinations:
            destination_code = self.resolve_destination_code(town)
        if not destination_code:
            return []
        key = f"hotelbeds:{self.environment}:{town}:{destination_code}:{checkin.isoformat()}:{checkout.isoformat()}:{config.adults}"
        cached = self.cache.get(key)
        if cached is None:
            cached = self._fetch(destination_code, checkin, checkout, config)
            self.cache.set(key, cached)
        return [self._candidate_from_hotelbeds(row, town, night) for row in cached]

    def resolve_destination_code(self, town: str) -> str | None:
        cache_key = f"hotelbeds-destinations:{self.environment}:US"
        cached = self.cache.get(cache_key)
        if cached is None:
            cached = self._fetch_destinations()
            self.cache.set(cache_key, cached)
        town_name = town.split(",", 1)[0].strip().lower()
        exact = [
            row
            for row in cached
            if str(row.get("name", "")).strip().lower() == town_name
        ]
        if exact:
            return str(exact[0].get("code"))
        partial = [
            row
            for row in cached
            if town_name in str(row.get("name", "")).lower()
            or str(row.get("name", "")).lower() in town_name
        ]
        if partial:
            return str(partial[0].get("code"))
        return None

    def _fetch_destinations(self) -> list[dict]:
        base_url = (
            "https://api.hotelbeds.com"
            if self.environment == "live"
            else "https://api.test.hotelbeds.com"
        )
        params = urllib.parse.urlencode(
            {
                "fields": "ALL",
                "language": "ENG",
                "countryCodes": "US",
                "limit": "1000",
            }
        )
        url = f"{base_url}/hotel-content-api/1.0/locations/destinations?{params}"
        request = urllib.request.Request(
            url,
            headers={
                "Accept": "application/json",
                "Api-key": self.api_key or "",
                "X-Signature": self._signature(),
            },
            method="GET",
        )
        with urllib.request.urlopen(request, timeout=30) as response:
            payload = json.loads(response.read().decode("utf-8"))
        if isinstance(payload, list):
            return payload
        destinations = payload.get("destinations")
        if isinstance(destinations, list):
            return destinations
        return []

    def _fetch(self, destination_code: str, checkin: date, checkout: date, config: SearchConfig) -> list[dict]:
        base_url = (
            "https://api.hotelbeds.com"
            if self.environment == "live"
            else "https://api.test.hotelbeds.com"
        )
        url = f"{base_url}/hotel-api/1.0/hotels"
        body = json.dumps(
            {
                "stay": {
                    "checkIn": checkin.isoformat(),
                    "checkOut": checkout.isoformat(),
                },
                "occupancies": [
                    {
                        "rooms": 1,
                        "adults": config.adults,
                        "children": 0,
                    }
                ],
                "destination": {
                    "code": destination_code,
                },
            }
        ).encode("utf-8")
        request = urllib.request.Request(
            url,
            data=body,
            headers={
                "Accept": "application/json",
                "Content-Type": "application/json",
                "Api-key": self.api_key or "",
                "X-Signature": self._signature(),
            },
            method="POST",
        )
        with urllib.request.urlopen(request, timeout=30) as response:
            payload = json.loads(response.read().decode("utf-8"))
        hotels = payload.get("hotels") or {}
        return hotels.get("hotels", [])[:20]

    def _signature(self) -> str:
        raw = f"{self.api_key}{self.secret}{int(time.time())}"
        return hashlib.sha256(raw.encode("utf-8")).hexdigest()

    def _candidate_from_hotelbeds(self, row: dict, town: str, night: int) -> HotelCandidate:
        name = str(row.get("name") or f"Hotelbeds hotel {row.get('code', '')}".strip())
        price = parse_price(row.get("minRate")) or 9999
        category = str(row.get("categoryName") or row.get("categoryCode") or "")
        rating = hotelbeds_category_to_rating(category)
        rooms = row.get("rooms") or []
        rates_text = json.dumps(rooms).lower()
        return HotelCandidate(
            night=night,
            town=town,
            name=name,
            price=price,
            rating=rating,
            reviews=100,
            detour_miles=3.0,
            detour_minutes=10.5,
            free_cancellation="cancellationpolicies" in rates_text,
            parking="parking" in json.dumps(row).lower(),
            address=str(row.get("zoneName") or row.get("destinationName") or town),
            link=maps_search_url(name, town),
            source="hotelbeds",
            review_snippet="Hotelbeds availability result; cross-check Google reviews before booking.",
        )


def load_hotelbeds_destination_codes() -> dict[str, str]:
    raw = os.environ.get("HOTELBEDS_DESTINATION_CODES_JSON")
    if not raw:
        return {}
    try:
        payload = json.loads(raw)
    except json.JSONDecodeError:
        return {}
    return {str(key): str(value) for key, value in payload.items()}


def hotelbeds_category_to_rating(category: str) -> float:
    digits = [int(ch) for ch in category if ch.isdigit()]
    if digits:
        return clamp(float(max(digits)), 3.2, 5.0)
    upper = category.upper()
    if "SUPERIOR" in upper or "LUXURY" in upper:
        return 4.0
    if "HOSTEL" in upper or "APARTHOTEL" in upper:
        return 3.4
    return 3.5


class GoogleRoutesDistanceProvider:
    """Optional live route distance for fuel estimates."""

    def __init__(self, cache: Cache) -> None:
        self.cache = cache
        self.api_key = os.environ.get("GOOGLE_MAPS_API_KEY") or os.environ.get("GOOGLE_ROUTES_API_KEY")

    def available(self) -> bool:
        return bool(self.api_key)

    def route_miles(self, config: SearchConfig) -> float | None:
        if not self.api_key:
            return None
        key = f"google-routes:{config.origin}:{config.destination}:{config.route}"
        cached = self.cache.get(key)
        if cached is not None and cached:
            return float(cached[0]["miles"])
        miles = self._fetch(config)
        if miles:
            self.cache.set(key, [{"miles": miles}])
        return miles

    def _fetch(self, config: SearchConfig) -> float | None:
        url = "https://routes.googleapis.com/directions/v2:computeRoutes"
        body = json.dumps(
            {
                "origin": {"address": config.origin},
                "destination": {"address": config.destination},
                "intermediates": [{"address": town} for town in route_intermediates(config.route)],
                "travelMode": "DRIVE",
                "routingPreference": "TRAFFIC_UNAWARE",
                "computeAlternativeRoutes": False,
                "routeModifiers": {"avoidTolls": False, "avoidHighways": False},
                "languageCode": "en-US",
                "units": "IMPERIAL",
            }
        ).encode("utf-8")
        headers = {
            "Content-Type": "application/json",
            "X-Goog-Api-Key": self.api_key or "",
            "X-Goog-FieldMask": "routes.distanceMeters,routes.duration",
        }
        request = urllib.request.Request(url, data=body, headers=headers, method="POST")
        with urllib.request.urlopen(request, timeout=30) as response:
            payload = json.loads(response.read().decode("utf-8"))
        routes = payload.get("routes") or []
        if not routes:
            return None
        meters = routes[0].get("distanceMeters")
        return round(float(meters) / 1609.344, 1) if meters else None


def route_intermediates(route: str) -> list[str]:
    if route == "southern-i40":
        return ["Wytheville, VA", "Jackson, TN", "Clinton, OK", "Grants, NM"]
    return []


def parse_price(value: object) -> float | None:
    if isinstance(value, (int, float)):
        return float(value)
    if not value:
        return None
    cleaned = "".join(ch for ch in str(value) if ch.isdigit() or ch == ".")
    try:
        return float(cleaned)
    except ValueError:
        return None


def maps_search_url(name: str, town: str) -> str:
    return "https://www.google.com/maps/search/?" + urllib.parse.urlencode(
        {"api": "1", "query": f"{name} {town}"}
    )


def generate_stop_zones(config: SearchConfig) -> list[StopZone]:
    profile = ROUTE_PROFILES.get(config.route)
    if not profile:
        raise ValueError(
            f"Unknown route profile {config.route!r}. Available: {', '.join(ROUTE_PROFILES)}"
        )
    zones: list[StopZone] = []
    for night_data in profile[: config.nights]:
        for town in night_data["towns"]:
            zones.append(
                StopZone(
                    night=int(night_data["night"]),
                    town=town,
                    target_mile=int(TOWN_MILES.get(town, night_data["target_mile"])),
                )
            )
    return zones


def reject_reason(candidate: HotelCandidate, config: SearchConfig) -> str:
    snippet = candidate.review_snippet.lower()
    if candidate.rating < 3.2:
        return "rating below 3.2"
    if candidate.reviews < 100:
        return "fewer than 100 reviews"
    if candidate.price > max(config.max_nightly, 95):
        return "price above ceiling"
    if candidate.detour_minutes > 20:
        return "detour above 20 minutes"
    for term in BAD_REVIEW_TERMS:
        if term in snippet:
            return f"review risk: {term}"
    for avoid in config.avoid_terms:
        if avoid.lower() in f"{candidate.town} {candidate.address}".lower():
            return f"avoid area: {avoid}"
    return ""


def score_candidate(candidate: HotelCandidate, config: SearchConfig) -> float:
    price_score = clamp(1 - (candidate.price / max(config.max_nightly, 1)), 0, 1)
    detour_score = clamp(1 - (candidate.detour_minutes / 20), 0, 1)
    rating_score = clamp((candidate.rating - 3.2) / 1.8, 0, 1)
    review_score = clamp(math.log10(max(candidate.reviews, 1)) / 4, 0, 1)
    reputation_score = (rating_score * 0.65) + (review_score * 0.35)
    cancellation_score = 1.0 if candidate.free_cancellation else 0.25
    parking_score = 1.0 if candidate.parking else 0.0
    return round(
        price_score * 45
        + detour_score * 20
        + reputation_score * 20
        + cancellation_score * 10
        + parking_score * 5,
        2,
    )


def clamp(value: float, low: float, high: float) -> float:
    return max(low, min(high, value))


def collect_candidates(config: SearchConfig, providers: list[HotelProvider]) -> tuple[list[HotelCandidate], list[HotelCandidate]]:
    accepted: list[HotelCandidate] = []
    rejected: list[HotelCandidate] = []
    for zone in generate_stop_zones(config):
        checkin = config.checkin_date + timedelta(days=zone.night - 1)
        checkout = checkin + timedelta(days=1)
        town_results: list[HotelCandidate] = []
        for provider in providers:
            try:
                town_results.extend(provider.search(zone.town, zone.night, checkin, checkout, config))
            except urllib.error.HTTPError as exc:
                print(
                    f"Warning: {provider.__class__.__name__} skipped {zone.town} "
                    f"for night {zone.night}: HTTP {exc.code}",
                    file=sys.stderr,
                )
            except urllib.error.URLError as exc:
                print(
                    f"Warning: {provider.__class__.__name__} skipped {zone.town} "
                    f"for night {zone.night}: {exc.reason}",
                    file=sys.stderr,
                )
        deduped = dedupe_candidates(town_results)
        for candidate in deduped:
            candidate.rejected_reason = reject_reason(candidate, config)
            candidate.score = score_candidate(candidate, config)
            if candidate.rejected_reason:
                rejected.append(candidate)
            else:
                accepted.append(candidate)
    return accepted, rejected


def dedupe_candidates(candidates: Iterable[HotelCandidate]) -> list[HotelCandidate]:
    best_by_key: dict[str, HotelCandidate] = {}
    for candidate in candidates:
        key = normalize_key(candidate.name, candidate.town)
        existing = best_by_key.get(key)
        if not existing or candidate.source.startswith("serpapi") or candidate.price < existing.price:
            best_by_key[key] = candidate
    return list(best_by_key.values())


def normalize_key(name: str, town: str) -> str:
    return "".join(ch.lower() for ch in f"{name}:{town}" if ch.isalnum())


def choose_best_plan(candidates: list[HotelCandidate], config: SearchConfig, route_miles: float | None = None) -> TripPlan:
    by_night: dict[int, list[HotelCandidate]] = {}
    for candidate in candidates:
        by_night.setdefault(candidate.night, []).append(candidate)
    for night in by_night:
        by_night[night].sort(key=lambda c: (-c.score, c.price))

    if any(night not in by_night for night in range(1, config.nights + 1)):
        missing = [str(n) for n in range(1, config.nights + 1) if n not in by_night]
        raise RuntimeError(f"No acceptable hotels found for night(s): {', '.join(missing)}")

    states: list[tuple[list[HotelCandidate], float]] = [([], 0.0)]
    for night in range(1, config.nights + 1):
        next_states: list[tuple[list[HotelCandidate], float]] = []
        for chain, score in states:
            for hotel in by_night[night][:8]:
                new_chain = chain + [hotel]
                next_states.append((new_chain, score + chain_penalty(new_chain, config)))
        next_states.sort(key=lambda item: item[1])
        states = next_states[:80]

    best_chain, penalty = min(states, key=lambda item: item[1])
    hotel_total = round(sum(h.price for h in best_chain), 2)
    route_miles = route_miles or TOWN_MILES.get(config.destination, 2360) - TOWN_MILES.get(config.origin, 0)
    detour_miles = sum(h.detour_miles * 2 for h in best_chain)
    fuel_estimate = round((route_miles / config.mpg) * config.fuel_price, 2)
    detour_fuel_cost = round((detour_miles / config.mpg) * config.fuel_price, 2)
    remaining = round(config.budget - hotel_total - fuel_estimate - detour_fuel_cost, 2)
    daily = daily_mile_segments(best_chain, config)
    trip_score = round(hotel_total + detour_fuel_cost + penalty, 2)
    return TripPlan(best_chain, hotel_total, fuel_estimate, detour_fuel_cost, remaining, trip_score, daily)


def chain_penalty(chain: list[HotelCandidate], config: SearchConfig) -> float:
    hotel = chain[-1]
    penalty = hotel.price - hotel.score
    town_text = f"{hotel.town} {hotel.address}".lower()
    if any(term.lower() in town_text for term in config.avoid_terms):
        penalty += 1000
    for miles in daily_mile_segments(chain, config):
        if miles > 650:
            penalty += (miles - 650) * 1.25
        if miles < 300 and len(chain) > 1:
            penalty += (300 - miles) * 0.25
    return penalty


def daily_mile_segments(chain: list[HotelCandidate], config: SearchConfig) -> list[float]:
    miles = [TOWN_MILES.get(config.origin, 0)]
    miles.extend(TOWN_MILES.get(hotel.town, 0) for hotel in chain)
    if len(chain) == config.nights:
        miles.append(TOWN_MILES.get(config.destination, 2360))
    return [round(miles[i] - miles[i - 1], 1) for i in range(1, len(miles))]


def top_three_by_night(candidates: list[HotelCandidate]) -> dict[int, list[HotelCandidate]]:
    grouped: dict[int, list[HotelCandidate]] = {}
    for candidate in candidates:
        grouped.setdefault(candidate.night, []).append(candidate)
    return {
        night: sorted(rows, key=lambda c: (-c.score, c.price))[:3]
        for night, rows in grouped.items()
    }


def display_choices_for_night(
    candidates: list[HotelCandidate], selected: HotelCandidate | None
) -> list[HotelCandidate]:
    rows = sorted(candidates, key=lambda c: (-c.score, c.price))[:3]
    if selected and not any(same_hotel(selected, row) for row in rows):
        rows = [selected] + rows[:2]
    return rows


def same_hotel(left: HotelCandidate, right: HotelCandidate) -> bool:
    return left.night == right.night and left.town == right.town and left.name == right.name


def write_csv(path: Path, candidates: list[HotelCandidate]) -> None:
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(
            handle,
            fieldnames=[
                "night",
                "town",
                "name",
                "price",
                "rating",
                "reviews",
                "detour_miles",
                "detour_minutes",
                "free_cancellation",
                "parking",
                "score",
                "link",
                "source",
            ],
        )
        writer.writeheader()
        for candidate in sorted(candidates, key=lambda c: (c.night, -c.score, c.price)):
            writer.writerow({field: getattr(candidate, field) for field in writer.fieldnames})


def write_json(path: Path, config: SearchConfig, plan: TripPlan, candidates: list[HotelCandidate], rejected: list[HotelCandidate]) -> None:
    payload = {
        "config": {
            **asdict(config),
            "checkin_date": config.checkin_date.isoformat(),
            "output_dir": str(config.output_dir),
            "cache_path": str(config.cache_path),
        },
        "best_plan": serialize_plan(plan),
        "top_three_by_night": {
            str(night): [serialize_candidate(c) for c in rows]
            for night, rows in top_three_by_night(candidates).items()
        },
        "rejected": [serialize_candidate(c) for c in rejected],
    }
    path.write_text(json.dumps(payload, indent=2), encoding="utf-8")


def serialize_plan(plan: TripPlan) -> dict:
    return {
        "hotels": [serialize_candidate(hotel) for hotel in plan.hotels],
        "hotel_total": plan.hotel_total,
        "fuel_estimate": plan.fuel_estimate,
        "detour_fuel_cost": plan.detour_fuel_cost,
        "remaining_budget": plan.remaining_budget,
        "total_score": plan.total_score,
        "daily_miles": plan.daily_miles,
    }


def serialize_candidate(candidate: HotelCandidate) -> dict:
    return asdict(candidate)


def write_html(path: Path, config: SearchConfig, plan: TripPlan, candidates: list[HotelCandidate], rejected: list[HotelCandidate]) -> None:
    grouped = top_three_by_night(candidates)
    rows = []
    for night in range(1, config.nights + 1):
        selected = plan.hotels[night - 1]
        for rank, candidate in enumerate(display_choices_for_night(grouped.get(night, []), selected), start=1):
            chosen = same_hotel(candidate, selected)
            rows.append(
                f"""
                <tr class="{'chosen' if chosen else ''}">
                  <td>{night}</td>
                  <td>{rank}</td>
                  <td>{escape(candidate.town)}</td>
                  <td>{escape(candidate.name)}</td>
                  <td>${candidate.price:.0f}</td>
                  <td>{candidate.rating:.1f}</td>
                  <td>{candidate.reviews:,}</td>
                  <td>{candidate.detour_miles:.1f} mi</td>
                  <td>{'yes' if candidate.free_cancellation else 'check'}</td>
                  <td>{candidate.score:.1f}</td>
                  <td><a href="{escape(candidate.link)}">open</a></td>
                </tr>
                """
            )
    plan_cards = "\n".join(
        f"""
        <section class="stop">
          <div>
            <span>Night {hotel.night}</span>
            <h2>{escape(hotel.town)}</h2>
            <p>{escape(hotel.name)}</p>
          </div>
          <strong>${hotel.price:.0f}</strong>
          <a href="{escape(hotel.link)}">Map</a>
        </section>
        """
        for hotel in plan.hotels
    )
    rejected_rows = "\n".join(
        f"<tr><td>{r.night}</td><td>{escape(r.town)}</td><td>{escape(r.name)}</td><td>{escape(r.rejected_reason)}</td></tr>"
        for r in rejected[:40]
    )
    document = f"""<!doctype html>
<html lang="en">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <title>RoadScout report</title>
  <style>
    :root {{
      color-scheme: light;
      --ink: #1b1f23;
      --muted: #5f6b76;
      --line: #d7dde3;
      --paper: #f7f8f5;
      --panel: #ffffff;
      --accent: #126b5d;
      --warn: #8a4b11;
    }}
    body {{
      margin: 0;
      font: 15px/1.45 -apple-system, BlinkMacSystemFont, "Segoe UI", sans-serif;
      color: var(--ink);
      background: var(--paper);
    }}
    header {{
      padding: 28px 18px 18px;
      background: #24332f;
      color: white;
    }}
    main {{ max-width: 1120px; margin: 0 auto; padding: 18px; }}
    h1 {{ margin: 0 0 8px; font-size: 30px; letter-spacing: 0; }}
    h2 {{ margin: 0; font-size: 20px; letter-spacing: 0; }}
    .summary {{
      display: grid;
      grid-template-columns: repeat(auto-fit, minmax(160px, 1fr));
      gap: 10px;
      margin: 16px 0;
    }}
    .metric, .stop {{
      background: var(--panel);
      border: 1px solid var(--line);
      border-radius: 8px;
      padding: 12px;
    }}
    .metric span, .stop span {{ display: block; color: var(--muted); font-size: 12px; }}
    .metric strong {{ display: block; margin-top: 4px; font-size: 22px; }}
    .plan {{ display: grid; grid-template-columns: repeat(auto-fit, minmax(210px, 1fr)); gap: 10px; }}
    .stop {{ display: grid; grid-template-columns: 1fr auto; gap: 8px; align-items: center; }}
    .stop p {{ margin: 5px 0 0; color: var(--muted); }}
    .stop a {{ color: var(--accent); font-weight: 700; }}
    table {{
      width: 100%;
      border-collapse: collapse;
      background: var(--panel);
      border: 1px solid var(--line);
      border-radius: 8px;
      overflow: hidden;
    }}
    th, td {{ padding: 9px 8px; border-bottom: 1px solid var(--line); text-align: left; }}
    th {{ font-size: 12px; color: var(--muted); background: #eef2ef; }}
    tr.chosen td {{ background: #e7f4ee; }}
    a {{ color: #0f5f8f; }}
    .scroll {{ overflow-x: auto; margin: 14px 0 24px; }}
    .note {{ color: var(--muted); }}
    @media (max-width: 720px) {{
      body {{ font-size: 14px; }}
      h1 {{ font-size: 24px; }}
      th, td {{ padding: 8px 6px; white-space: nowrap; }}
    }}
  </style>
</head>
<body>
  <header>
    <h1>RoadScout</h1>
    <div>{escape(config.origin)} to {escape(config.destination)} via {escape(config.route)}</div>
  </header>
  <main>
    <section class="summary">
      <div class="metric"><span>Hotel estimate</span><strong>${plan.hotel_total:.0f}</strong></div>
      <div class="metric"><span>Fuel estimate</span><strong>${plan.fuel_estimate:.0f}</strong></div>
      <div class="metric"><span>Detour fuel</span><strong>${plan.detour_fuel_cost:.0f}</strong></div>
      <div class="metric"><span>Budget buffer</span><strong>${plan.remaining_budget:.0f}</strong></div>
    </section>
    <h2>Best chain</h2>
    <div class="plan">{plan_cards}</div>
    <p class="note">Daily mile segments: {", ".join(str(m) for m in plan.daily_miles)}. Highlighted rows are in the optimized chain.</p>
    <h2>Best 3 per night</h2>
    <div class="scroll">
      <table>
        <thead>
          <tr><th>Night</th><th>Rank</th><th>Town</th><th>Hotel</th><th>Price</th><th>Rating</th><th>Reviews</th><th>Detour</th><th>Cancel</th><th>Score</th><th>Link</th></tr>
        </thead>
        <tbody>{''.join(rows)}</tbody>
      </table>
    </div>
    <h2>Rejected checks</h2>
    <div class="scroll">
      <table>
        <thead><tr><th>Night</th><th>Town</th><th>Hotel</th><th>Reason</th></tr></thead>
        <tbody>{rejected_rows}</tbody>
      </table>
    </div>
  </main>
</body>
</html>
"""
    path.write_text(document, encoding="utf-8")


def escape(value: object) -> str:
    return html.escape(str(value), quote=True)


def print_report(config: SearchConfig, plan: TripPlan, candidates: list[HotelCandidate]) -> None:
    print("Best plan under ${:.0f}:".format(config.budget))
    print(f"Fuel estimate: ${plan.fuel_estimate:.0f}")
    print(f"Hotels estimate: ${plan.hotel_total:.0f}")
    print(f"Detour fuel estimate: ${plan.detour_fuel_cost:.0f}")
    print(f"Remaining buffer: ${plan.remaining_budget:.0f}")
    print()
    chosen = {(hotel.night, hotel.town, hotel.name) for hotel in plan.hotels}
    grouped = top_three_by_night(candidates)
    for night in range(1, config.nights + 1):
        selected = plan.hotels[night - 1]
        print(f"Night {night}: {selected.town}")
        for idx, candidate in enumerate(display_choices_for_night(grouped.get(night, []), selected), start=1):
            mark = "*" if same_hotel(candidate, selected) else " "
            cancel = "free cancellation" if candidate.free_cancellation else "check cancellation"
            print(
                f"{mark} {idx}. {candidate.name} - ${candidate.price:.0f} - "
                f"{candidate.rating:.1f} stars - {candidate.reviews:,} reviews - "
                f"{candidate.detour_miles:.1f} mi detour - {cancel}"
            )
        print()


def build_arg_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="RoadScout budget route lodging scanner",
        formatter_class=argparse.ArgumentDefaultsHelpFormatter,
    )
    parser.add_argument("--origin", default="Bethlehem, PA")
    parser.add_argument("--destination", default="Las Vegas, NV")
    parser.add_argument("--route", default="southern-i40", choices=sorted(ROUTE_PROFILES))
    parser.add_argument("--nights", type=int, default=4)
    parser.add_argument("--checkin-date", default=date.today().isoformat())
    parser.add_argument("--adults", type=int, default=1)
    parser.add_argument("--max-nightly", type=float, default=85)
    parser.add_argument("--budget", type=float, default=800)
    parser.add_argument("--mpg", type=float, required=True)
    parser.add_argument("--fuel-price", type=float, default=3.55)
    parser.add_argument("--search-radius", type=float, default=20)
    parser.add_argument("--avoid", action="append", default=[], help="Area to penalize or reject. Can be repeated.")
    parser.add_argument("--output-dir", type=Path, default=Path("roadscout_output"))
    parser.add_argument("--cache", type=Path, default=Path(".roadscout_cache.sqlite3"))
    parser.add_argument("--live-prices", action="store_true", help="Use SERPAPI_API_KEY when present.")
    parser.add_argument("--live-places", action="store_true", help="Use Google Places Text Search when GOOGLE_MAPS_API_KEY is present.")
    parser.add_argument("--live-route", action="store_true", help="Use Google Routes computeRoutes for the fuel distance when GOOGLE_MAPS_API_KEY is present.")
    parser.add_argument("--live-hotelbeds", action="store_true", help="Use Hotelbeds availability when HOTELBEDS_API_KEY, HOTELBEDS_SECRET, and destination codes are present.")
    parser.add_argument("--hotelbeds-env", choices=["test", "live"], default="test", help="Hotelbeds endpoint environment.")
    parser.add_argument("--hotelbeds-auto-destinations", action="store_true", help="Try to resolve US Hotelbeds destination codes from the Content API.")
    return parser


def parse_config(argv: list[str]) -> SearchConfig:
    args = build_arg_parser().parse_args(argv)
    try:
        checkin = datetime.strptime(args.checkin_date, "%Y-%m-%d").date()
    except ValueError as exc:
        raise SystemExit("--checkin-date must use YYYY-MM-DD") from exc
    if args.nights < 1 or args.nights > len(ROUTE_PROFILES[args.route]):
        raise SystemExit(f"--nights must be between 1 and {len(ROUTE_PROFILES[args.route])}")
    if args.mpg <= 0:
        raise SystemExit("--mpg must be greater than 0")
    avoid_terms = DEFAULT_AVOID_TERMS + list(args.avoid)
    return SearchConfig(
        origin=args.origin,
        destination=args.destination,
        route=args.route,
        nights=args.nights,
        checkin_date=checkin,
        adults=args.adults,
        max_nightly=args.max_nightly,
        budget=args.budget,
        mpg=args.mpg,
        fuel_price=args.fuel_price,
        search_radius=args.search_radius,
        avoid_terms=avoid_terms,
        output_dir=args.output_dir,
        cache_path=args.cache,
        live_prices=args.live_prices,
        live_places=args.live_places,
        live_route=args.live_route,
        live_hotelbeds=args.live_hotelbeds,
        hotelbeds_env=args.hotelbeds_env,
        hotelbeds_auto_destinations=args.hotelbeds_auto_destinations,
    )


def main(argv: list[str] | None = None) -> int:
    config = parse_config(argv or sys.argv[1:])
    config.output_dir.mkdir(parents=True, exist_ok=True)
    cache = Cache(config.cache_path)
    providers: list[HotelProvider] = []
    serpapi = SerpApiGoogleHotelsProvider(cache)
    if config.live_prices and serpapi.available():
        providers.append(serpapi)
    places = GooglePlacesTextSearchProvider(cache)
    if config.live_places and places.available():
        providers.append(places)
    hotelbeds = HotelbedsAvailabilityProvider(cache, config.hotelbeds_env)
    if config.live_hotelbeds and hotelbeds.available():
        providers.append(hotelbeds)
    providers.append(OfflineHotelProvider())

    accepted, rejected = collect_candidates(config, providers)
    routes = GoogleRoutesDistanceProvider(cache)
    live_route_miles = routes.route_miles(config) if config.live_route and routes.available() else None
    plan = choose_best_plan(accepted, config, live_route_miles)
    write_csv(config.output_dir / "best_hotels.csv", accepted)
    write_json(config.output_dir / "trip_budget.json", config, plan, accepted, rejected)
    write_html(config.output_dir / "best_hotels.html", config, plan, accepted, rejected)
    print_report(config, plan, accepted)
    print(
        textwrap.dedent(
            f"""
            Wrote:
              {config.output_dir / "best_hotels.html"}
              {config.output_dir / "best_hotels.csv"}
              {config.output_dir / "trip_budget.json"}
            """
        ).strip()
    )
    if config.live_prices and not serpapi.available():
        print("Note: --live-prices was set, but SERPAPI_API_KEY is missing; used offline seed data.")
    if config.live_places and not places.available():
        print("Note: --live-places was set, but GOOGLE_MAPS_API_KEY/GOOGLE_PLACES_API_KEY is missing.")
    if config.live_route and not routes.available():
        print("Note: --live-route was set, but GOOGLE_MAPS_API_KEY/GOOGLE_ROUTES_API_KEY is missing.")
    if config.live_hotelbeds:
        reason = hotelbeds.missing_reason()
        if reason:
            print(f"Note: --live-hotelbeds was set, but {reason}.")
        elif not hotelbeds.destination_codes and not config.hotelbeds_auto_destinations:
            print("Note: --live-hotelbeds was set, but HOTELBEDS_DESTINATION_CODES_JSON is missing.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
