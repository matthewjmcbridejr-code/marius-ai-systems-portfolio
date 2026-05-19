# McTable

*Filesystem and GitHub coordination layer for agents.*

Treats agent output as auditable artifacts rather than opaque API calls. Every task has an ID. Every proposed change has a proof bundle. Every code change ships as a reviewable pull request. The data shape is the durable record.

## What it does

Sits underneath the Marius platform as the coordination layer between operator intent and agent execution:

- **Task records.** Every agent run starts from a task with a stable ID, a spec, an assigned agent, and a state machine state. Task records survive process restarts, queue drains, and operator handoffs.
- **Proof bundles.** Before an agent proposes a change, it assembles a bundle: which files it read, which lines it cited, which searches it ran, which alternatives it considered, and the short reasoning summary that led to the proposal. The bundle is referenced from the PR and queryable from the dashboard.
- **Activity log.** A per-agent, append-only stream of what each agent has done over time. "What did agent X do last Tuesday?" has a real answer.
- **Pull request workflow.** Code-side effects don't land on `main` directly. They land on a branch, get a PR with the task ID and rationale in the description, and a human merges.

## Why this matters

Most agent observability is a transcript of the agent's chain-of-thought. That's interesting for debugging but useless for accountability. A transcript doesn't tell you what the agent *did* — only what it said it was doing.

McTable captures the side-effect side of the ledger: artifacts produced, references touched, branches created, PRs opened, scores logged. The agent's reasoning trace is attached but not the source of truth.

This is the layer that makes "the system did X" a question with a definitive answer.

## Architecture

- JSON Schema for the task record, proof bundle, and activity entry shapes.
- GitHub REST and GraphQL APIs for branch, commit, PR, and review status operations.
- An append-only log store (queryable by task ID, agent, time range).
- A lightweight web UI for the operator: live task state, recent activity, approval queue.

## Stack

Python, GitHub REST/GraphQL APIs, JSON Schema, structured logging, simple web UI.

## Status

Private. Used as the coordination layer for all Marius platform work and as a model for how agent output should be structured downstream.
