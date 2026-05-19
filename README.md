# marius-ai-systems-portfolio

A sanitized public portfolio of AI systems work by **Matt McBride**.

This repository is a public-facing companion to private multi-agent AI systems work. It is intended to demonstrate architecture, workflow design, evaluation thinking, and AI systems operations — without exposing the underlying production code or any private operational details.

---

## Start Here

- **[`projects/`](./projects/)** — appetizer pages for the eight projects this portfolio is drawn from. One file per project. Read these first.
- **[`docs/architecture.md`](./docs/architecture.md)** — cross-cutting system architecture for the Marius platform: gateway, provider routing, policy layer, task coordination, evaluation, dashboard.
- **[`docs/workflow_examples.md`](./docs/workflow_examples.md)** — four representative agent workflow patterns.
- **[`docs/evaluation_and_safety.md`](./docs/evaluation_and_safety.md)** — evaluation rubric design and the safety principles the systems are built around.
- **[`examples/`](./examples/)** — representative schemas: an agent task packet, a provider status snapshot, an evaluation rubric format.

## The Projects

| Project | One-liner | Status |
|---|---|---|
| [Marius Mind](./projects/marius-mind.md) | Multi-agent orchestration and control plane | Private |
| [Marius Code](./projects/marius-code.md) | Code-reading and PR-proposing agent | Private |
| [Marius Trader](./projects/marius-trader.md) | Paper-only AI trading research cockpit | Research |
| [Marius Radar](./projects/marius-radar.md) | OSINT-driven prospect intelligence engine | Private |
| [Marius Foreman](./projects/marius-foreman.md) | Missed-call recovery system for contractors | Live |
| [McTable](./projects/mctable.md) | Filesystem + GitHub coordination layer for agents | Private |
| [Lead Leak Scan](./projects/lead-leak-scan.md) | SMB website audit tool | Live |
| [Good Stuff Vault](./projects/good-stuff-vault.md) | Portfolio of 12 paywalled curated sites | Live |

## What Is Intentionally Excluded

- `.env` files, API keys, tokens, secrets of any kind
- Private logs, run transcripts, or trace dumps
- Real client, customer, or prospect data
- Trading execution code, broker API integrations, or live order routing
- Internal domain names, private repository names, or operational hostnames
- Any business-sensitive contract, pricing, or revenue details

## Background

I have hands-on experience building Python / FastAPI services, integrating with multiple LLM providers (cloud and local), designing evaluation pipelines, and operating systems on Linux servers. I also bring real-world operational leadership from running teams in non-software environments, which shapes how I think about safety gates, audit trails, and human review.

I am applying this experience to AI training, agent-builder, LLM evaluation, and software workflow roles.

## Contact

- **Email:** matt@usemarius.com
- **GitHub:** [github.com/matthewjmcbridejr-code](https://github.com/matthewjmcbridejr-code)
- **Personal page:** [usemarius.com/matthewmcbride](https://usemarius.com/matthewmcbride)

---

*This portfolio is a manicured public reflection of private work. Where you see "Marius" in this repo, treat it as a label for an architectural pattern, not a claim that any specific production system is publicly available.*
