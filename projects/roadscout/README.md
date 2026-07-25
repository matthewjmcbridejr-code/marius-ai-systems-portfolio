# RoadScout

RoadScout is a budget route lodging scanner. It is designed for a specific road trip workflow:

1. Generate overnight stop zones along a route.
2. Search cheap hotels/motels near each zone.
3. Reject risky options.
4. Score the survivors by price, detour, reviews, cancellation, and parking.
5. Pick a whole-trip hotel chain that keeps each day driveable.
6. Write phone-friendly `HTML`, `CSV`, and `JSON` reports.

## Quick start

```bash
python roadscout.py \
  --origin "Bethlehem, PA" \
  --destination "Las Vegas, NV" \
  --route "southern-i40" \
  --nights 4 \
  --checkin-date "2026-05-27" \
  --adults 1 \
  --budget 800 \
  --max-nightly 85 \
  --mpg 25
```

Outputs are written to `roadscout_output/`:

- `best_hotels.html`
- `best_hotels.csv`
- `trip_budget.json`

## Live APIs

The scanner works offline with deterministic sample data. To use SerpAPI Google Hotels for live-ish prices:

```bash
set SERPAPI_API_KEY=your_key_here
python roadscout.py --mpg 25 --live-prices
```

To add Google Places candidate discovery:

```bash
set GOOGLE_MAPS_API_KEY=your_key_here
python roadscout.py --mpg 25 --live-places
```

To use Google Routes `computeRoutes` for the fuel-distance estimate:

```bash
set GOOGLE_MAPS_API_KEY=your_key_here
python roadscout.py --mpg 25 --live-route
```

To add Hotelbeds availability as a backup supplier, set an API key, shared secret, and destination-code mapping:

```bash
set HOTELBEDS_API_KEY=your_key_here
set HOTELBEDS_SECRET=your_secret_here
set HOTELBEDS_DESTINATION_CODES_JSON={"Wytheville, VA":"DEST_CODE"}
python roadscout.py --mpg 25 --live-hotelbeds --hotelbeds-env test
```

Or let RoadScout try to resolve US destination codes from the Hotelbeds Content API:

```bash
python roadscout.py --mpg 25 --live-hotelbeds --hotelbeds-auto-destinations
```

Hotelbeds authentication requires an `Api-key` header and an `X-Signature` SHA256 hash generated from API key + secret + current Unix timestamp. Hotelbeds availability uses destination or hotel codes rather than plain town names, so RoadScout either needs `HOTELBEDS_DESTINATION_CODES_JSON` or `--hotelbeds-auto-destinations` before it can query a town.

API results are cached in `.roadscout_cache.sqlite3`. Google Places candidates use the nightly ceiling as a placeholder price because Places does not reliably return live nightly rates; pair it with `--live-prices` for real price discovery.

## Current route profile

`southern-i40` uses the stop zones discussed for Bethlehem, PA to Las Vegas, NV:

- Night 1: Wytheville VA, Bristol TN, Kingsport TN
- Night 2: Dickson TN, Jackson TN, Brownsville TN
- Night 3: Weatherford OK, Clinton OK, Elk City OK
- Night 4: Grants NM, Gallup NM, Holbrook AZ

## Rejection rules

RoadScout rejects hotels when:

- rating is below `3.2`
- review count is below `100`
- price is above the nightly ceiling, with an absolute fallback ceiling of `$95`
- detour is above `20` minutes
- review text includes risk terms such as bugs, break-ins, unsafe, dirty sheets, or stolen
- the hotel falls inside an avoid term

## Scoring

Candidate score:

```txt
price_score * 0.45
+ distance_from_route_score * 0.20
+ review_score * 0.20
+ cancellation_score * 0.10
+ parking_score * 0.05
```

Trip-chain scoring also penalizes overlong driving days, too-short intermediate hops, detour fuel, avoid areas, and total hotel cost.
