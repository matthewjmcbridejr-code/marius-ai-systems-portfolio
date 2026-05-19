# Good Stuff Vault

*Portfolio of 12 paywalled curated digital product sites. Live at [goodstuffvault.com](https://goodstuffvault.com).*

A multi-niche bundle of paywalled curated resource sites — each in a distinct vertical, each with its own visual identity, all built from a single codebase that compiles to twelve distinct-looking sites.

## What it is

Each vault is a self-contained product:

- A landing page selling the vault.
- A free preview surfacing a handful of curated picks ("you wouldn't pay if you didn't see the quality").
- A gated content vault behind a Stripe Payment Link, accessed by a unique slug URL after checkout.
- $19–$29 lifetime access.

The twelve live vaults span AI tools, productivity stacks, careers, content creators, indie hackers, sales, weddings, plants, beauty and skincare, wellness, money for parents, and dogs. About 4,200 curated resources in total.

## What's interesting

The interesting work isn't the curation — it's the build pipeline.

- **One template, twelve themes.** Each vault shares the same structural HTML and the same component primitives. The visual identity per niche — typography, palette, dark vs. light mode, hero photography style — lives in CSS variables tuned to each audience. Lifestyle vaults read like editorial magazines; tech vaults read like developer docs.
- **Data-driven content.** Curated resources live as JSON. A Python builder takes the JSON, the template, and the per-niche theme variables, and emits a complete deployable site. Adding a new resource is a JSON edit; adding a new vault is an hour of config plus the curation.
- **Mini-apps.** Several vaults include embedded mini-apps (a wedding budget splitter, a YouTube title scorer, a resume keyword-match checker) that share the same CSS variable system, so they auto-theme to the surrounding vault.
- **Deploy infrastructure.** Vercel project deploys via API, with full-route crawls before every deploy to prevent the file-based deploy model from accidentally removing live pages.
- **Payment infrastructure.** Each vault has its own Stripe product, Stripe Payment Link, success page, and gated content URL. An affiliate program with master coupon and tracked promo codes runs across the portfolio.

## What's not interesting (deliberately)

The system makes individual vault economics small. Each vault sells in the low thousands per month at peak. The portfolio works because the per-vault unit economics are not the point — the build pipeline and the cross-niche distribution surface are.

## Stack

Python build pipeline, custom HTML/CSS template system with per-niche CSS variables, Vercel API for file-based deploys, Stripe Payment Links + Stripe coupons/promotion codes, Namecheap for DNS, embedded mini-apps in vanilla JS.

## Status

**Live at [goodstuffvault.com](https://goodstuffvault.com).** Twelve vaults deployed, approximately 4,200 curated resources, with active marketing across X, Reddit, and Pinterest.
