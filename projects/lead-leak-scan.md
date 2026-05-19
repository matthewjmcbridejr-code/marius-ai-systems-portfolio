# Lead Leak Scan

*Free SMB website-audit tool. Live at [missedleadscan.com](https://missedleadscan.com).*

A public scanner that grades local home-services businesses on fifteen specific signals tied to missed-lead revenue. The free scan creates demand for paid audits and ongoing monitoring.

## What it does

A small business owner pastes their domain — bare, no scheme required ("yourbusiness.com" is fine). The scanner runs a parallel audit across fifteen signals and returns a scored report within ~30 seconds.

The fifteen signals were chosen because each has a measurable revenue impact for local home-services businesses. Examples:

- Mobile page-load performance (Core Web Vitals).
- Google Business Profile completeness and review velocity.
- Local SERP rank for the three most common services in the operator's category.
- Mobile click-to-call presence and accessibility.
- Schema markup for LocalBusiness, Service, and Review types.
- Contact form friction.
- HTTPS, basic security hygiene, and exposed credential checks.

The report doesn't just flag what's wrong — it explains the revenue translation. "Your mobile page loads in 6 seconds. Industry benchmark is 2.5. Estimated bounce-rate cost: ~X leads per month."

## Tiers

- **Free Scan** — the fifteen-signal audit. No account required.
- **Audit Pro** ($149) — deeper analysis including competitor comparison and a prioritized fix list.
- **Monitoring** ($49 / month) — recurring scans, signal drift alerts, monthly delta reports.

## Architecture

- Next.js 14 (App Router), TypeScript.
- Vercel deploy with edge-cached static routes for the marketing pages and serverless functions for the scanner.
- Signal collectors run in parallel: Google PageSpeed, Google Places, SerpAPI, Shodan, HIBP, Tavily for AI-based fact-finding, Firecrawl for HTML scrape.
- Decodo residential proxy network for SERP and rank-tracking calls that wouldn't survive datacenter IPs.
- Stripe Payment Links for paid tiers, with checkout flow redirecting to a result-unlock view.

## What's interesting

The free scan is the funnel. The fifteen signals are intentionally tied to things the operator can *act on* — not vanity metrics. "Your domain isn't an LLC" is unactionable; "your mobile call button is below the fold and 30% smaller than the recommended tap target" is a fix the operator can implement in an afternoon.

## Stack

Next.js 14, TypeScript, Vercel, Stripe, Google PageSpeed API, Google Places API, SerpAPI, Shodan, HIBP, Tavily, Firecrawl, Decodo proxy network.

## Status

**Live at [missedleadscan.com](https://missedleadscan.com).** Free scan available without account.
