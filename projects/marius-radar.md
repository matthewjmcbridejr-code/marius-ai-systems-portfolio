# Marius Radar

*OSINT-driven prospect intelligence engine.*

A lead intelligence layer that scores prospects on operational signals other tools miss. Built on a data fabric of public OSINT sources, surfaced to outreach via scored "ready-to-pitch" leads.

## What it does

Most lead-intel tools score on **firmographic** data: revenue, headcount, industry, funding stage. Anyone selling to a prospect sees the same data and reaches the same conclusions.

Radar scores on **operational** signals:

- Site performance (Core Web Vitals, mobile usability).
- Local SERP position and presence (Google Business Profile completeness, review velocity).
- Exposed services and known credential leaks (sourced from breach databases).
- Schema markup, contact accessibility, basic SEO hygiene.
- Recent technology changes (new front-end framework, swapped CMS, etc.).

Each signal carries a known revenue implication for the prospect's category. The composite score reflects "how much money this business is leaving on the table that the right vendor could fix."

## Architecture

- **Signal collectors** — small async workers per signal source. Each writes normalized records to a shared store.
- **Aggregator** — joins records by prospect, computes the composite score, attaches actionability metadata.
- **Freshness layer** — re-scores prospects on a cadence, flags signal drift.
- **Outreach surface** — a queryable view: "show me high-score prospects in vertical X within geo Y where signal Z is true."

## What's interesting

The interesting trade-off is **signal recency vs. cost**. Some signals are cheap and stable (schema markup, page count). Some are expensive and volatile (site speed, breach exposure). The collector schedule adapts: stable signals refresh weekly, volatile ones daily, and the freshness layer flags when a high-score lead's defining signal is older than the score implies.

## Stack

Python, multiple OSINT API SDKs (Google PageSpeed, Google Places, SerpAPI, Shodan, HIBP, IntelX, Decodo proxy network, Firecrawl for HTML), async pipelines, queryable signal store.

## Status

Private engine. Surfaced indirectly through the public product [Lead Leak Scan](./lead-leak-scan.md), which uses a subset of the signals as a free entry point for SMB prospects.
