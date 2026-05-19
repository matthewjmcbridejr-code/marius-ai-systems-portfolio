# Project Summaries

Brief sanitized descriptions of the projects this portfolio is based on.

---

## Marius AI Systems Platform

**Status:** Private. Production code not included in this repo.

**What it is:** A multi-agent AI orchestration and control framework. Routes requests across LLM providers (cloud and local), enforces a policy layer over agent actions, coordinates multi-step tasks, and surfaces state through an operator dashboard.

**My role:** Architect and primary builder. Designed the gateway, the routing abstraction, the policy layer, the task state machine, and the evaluation/logging schema. Wrote the FastAPI services, the agent runners, and the dashboard backend.

**Stack:** Python, FastAPI, Pydantic, async HTTP, multiple LLM provider SDKs, structured logging, GitHub APIs, Linux server operations.

**Why it exists:** To make multi-agent work safe enough to run continuously, by keeping a human in the loop on the actions that matter.

---

## McTable Operator Layer

**Status:** Private. Concept and structure documented here only.

**What it is:** A filesystem and GitHub-oriented coordination layer that lives on top of the Marius platform. Tracks agent task assignments, the proof bundles each task produced, an activity log per agent, and a human-reviewed pull request workflow for any change that touches a repository.

**My role:** Designed the data shape (task records, proof bundles, activity entries), wrote the integration with GitHub's API for PR creation and review status, and built the operator-facing views that surface assignment state and recent activity.

**Stack:** Python, GitHub REST and GraphQL APIs, JSON Schema for the task and proof-bundle shapes, lightweight web UI for the operator view.

**Why it exists:** To treat agent output as auditable artifacts. If an agent did something, there is a row that says so, a bundle that explains why, and a PR a human can read.

---

## Contractor Communication Automation

**Status:** Concept work. Built around real workflows for small home-services contractors.

**What it is:** Practical automation for missed-call text-back, lead qualification, estimate follow-up, review request prompting, and lightweight CRM-style pipeline tracking. Designed for operators who do not want to run a complicated app — the system installs against the tools they already use.

**My role:** Designed the workflow patterns (when to send, what to ask, how to escalate), drafted the response templates, and laid out the integration points with phone, calendar, and review platforms.

**Stack:** Python, webhook handlers, SMS provider APIs, calendar APIs, simple state machines per lead.

**Why it relates to AI systems:** The "agent drafts a response, operator approves before send" pattern from this project is the same pattern I use for any outbound communication from an automated system. Drafts not sends. Review queue not direct fire.

---

## Paper-Only AI Trading Research Cockpit

**Status:** Research project. Not a live trading system. Will not become a live trading system without a separate, deliberate review.

**What it is:** A committee-style analysis framework for evaluating trade ideas. Multiple agent personas (bull, bear, risk) analyze the same input. A judging agent summarizes the views and produces a structured paper recommendation. Outcomes are logged and later scored against what actually happened, to build an evaluation history of how the committee performs.

**My role:** Designed the committee structure, the judging prompt, the paper-outcome data model, and the historical scoring pipeline.

**Stack:** Python, LLM provider SDKs, structured JSON for paper recommendations, historical market data for scoring (read-only).

**Why it exists:** To study how multi-agent reasoning performs on a hard task with a clear ground truth — without ever putting real money at risk. The architectural deliberate-non-execution is the point.

---

## Notes on This Portfolio

Each of these projects has private code, private logs, and (in the case of the contractor and trading work) private context I am not at liberty to share. This repo is a reflection of how I think about and build these systems, not a release of the systems themselves.

Where a real artifact would be private, I have included a representative example file in the `examples/` directory.
