# McTable

*Agent operations control plane for proof-gated AI software work. Public surface: [mctable.team](https://mctable.team).*

McTable treats agent output as auditable artifacts rather than opaque chat transcripts or unreviewed code changes. Every task has an ID. Every proposed change has a proof bundle. Every code change ships as a reviewable pull request. The data shape is the durable record.

Public site: [mctable.team](https://mctable.team)

## What it does

McTable sits between operator intent and agent execution:

- **Task records.** Every agent run starts from a task with a stable ID, a spec, an assigned agent, and a state machine state. Task records survive process restarts, queue drains, and operator handoffs.
- **Proof bundles.** Before an agent proposes a change, it assembles evidence: which files it read, which lines it cited, which searches it ran, which alternatives it considered, and what it changed.
- **Activity log.** A per-agent, append-only stream of what each agent has done over time. “What did agent X do last Tuesday?” has a real answer.
- **Pull request workflow.** Code-side effects do not land on `main` directly. They land on a branch, get a PR with a task ID and rationale, and a human merges.
- **Authority firewall.** Emotional language, urgency, and praise do not grant execution authority. High-risk actions require explicit approval plus objective checks.

## Why this matters

Most agent tooling treats a transcript as the source of truth. That is not enough for software operations. A transcript says what the agent claimed it was doing; McTable records what changed, what was reviewed, what was blocked, and what was approved.

This is the layer that makes “the system did X” a question with a definitive answer.

## Architecture

- JSON Schema for task records, proof bundles, activity entries, and approval decisions.
- GitHub REST and GraphQL APIs for branch, commit, PR, and review status operations.
- Append-only local activity and proof stores.
- Lightweight operator UI for repo state, task state, recent activity, approvals, and PR review.
- Policy gates for destructive actions, merges, deploys, spending, and external communication.

## Stack

Python, FastAPI, GitHub REST/GraphQL APIs, JSON Schema, SQLite-style local state, structured logging, simple web UI, webhook integrations.

## Status

Private implementation with public positioning at [mctable.team](https://mctable.team). Used as the coordination layer for Marius platform work and as a model for how agent output should be structured downstream.