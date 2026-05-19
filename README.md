# marius-ai-systems-portfolio

A sanitized public portfolio of AI systems work by **Matt McBride**.

This repository is a public-facing companion to a private multi-agent AI orchestration project called Marius. It is intended to demonstrate architecture, workflow design, evaluation thinking, and AI systems operations — without exposing the underlying production code or any private operational details.

---

## What This Repo Is

A documentation-and-examples package showing how I think about and build:

- Multi-agent AI systems with provider routing and policy gates
- LLM evaluation pipelines and rubric-based scoring
- Filesystem and GitHub-oriented coordination layers for agents
- Operator-facing dashboards and audit trails
- Human-in-the-loop pull request workflows for agent-generated changes

## What This Repo Is Not

- **Not the production code.** The real Marius system runs in private repositories and is not included or referenced here.
- **Not a runnable application.** The examples are illustrative — schemas, structures, and rubric formats — not a working system you can clone and start.
- **Not a vendor pitch.** No client work, no testimonials, no metrics, no contractor sales material lives here.

## What Is Intentionally Excluded

- `.env` files, API keys, tokens, secrets of any kind
- Private logs, run transcripts, or trace dumps
- Real client, customer, or prospect data
- Trading execution code, broker API integrations, or live order routing
- Internal domain names, private repository names, or operational hostnames
- Any business-sensitive contract, pricing, or revenue details

## Repository Contents

```
.
├── README.md                          (this file)
├── docs/
│   ├── architecture.md                System architecture and component design
│   ├── workflow_examples.md           Representative agent workflow patterns
│   ├── evaluation_and_safety.md       Evaluation rubric design and safety gates
│   └── project_summaries.md           Brief sanitized summaries of related work
└── examples/
    ├── agent_task_packet.example.json     Shape of a coordinated agent task
    ├── provider_status.example.json       Shape of a provider routing/status record
    └── evaluation_rubric.example.md       Example rubric format for output scoring
```

## Background

I have hands-on experience building Python / FastAPI services, integrating with multiple LLM providers (cloud and local), designing evaluation pipelines, and operating systems on Linux servers. I also bring real-world operational leadership from running teams in non-software environments, which shapes how I think about safety gates, audit trails, and human review.

I am applying this experience to AI training, agent-builder, LLM evaluation, and software workflow roles.

## Contact

- **Email:** matt@usemarius.com
- **GitHub:** [github.com/matthewjmcbridejr-code](https://github.com/matthewjmcbridejr-code)
- **Personal page:** [usemarius.com/matthewmcbride](https://usemarius.com/matthewmcbride)

---

*This portfolio is a manicured public reflection of private work. Where you see "Marius" in this repo, treat it as a label for an architectural pattern, not a claim that any specific production system is publicly available.*
