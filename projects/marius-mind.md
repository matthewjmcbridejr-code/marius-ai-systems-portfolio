# Marius Mind

*Multi-agent orchestration and control plane.*

The brain of the Marius platform. Decides which model handles a request, what policy gates apply to an agent's proposed action, how multi-step work coordinates, and how every run gets logged and scored.

## What it does

Receives task requests from an operator (or from another agent), routes them across cloud and local LLM providers, evaluates proposed actions against a declarative policy layer, coordinates multi-step workflows as a state machine, and surfaces everything through an operator dashboard.

Action gates default to **require approval**, not **allow**. Autonomy is granted explicitly per action type, not inherited.

## Architecture

- **FastAPI gateway** — auth, request validation (Pydantic), per-route rate limiting. Thin layer, no business logic.
- **Provider routing** — picks the model for a task based on task type, cost ceiling, recent provider error rate, and explicit operator overrides. Cloud and local models live behind the same abstraction.
- **Policy layer** — declarative rules (allow / require-approval / deny) evaluated before any side effect. Unknown action types route to approval queue, not to the model.
- **Task coordinator** — explicit state machine: `queued → running → awaiting_review → completed | failed | cancelled`. Restarts are idempotent.
- **Evaluation and logging** — every model call writes a structured, append-only log row with rubric scores, token usage, latency, and a reference to the proof bundle the agent assembled.
- **Operator dashboard** — read-mostly. Live task feed, approval queue, recent eval-score trends, links to PRs and logs.

## What's interesting

The policy layer is the place to look. It's not a rule engine bolted on after the fact — it sits in front of every side effect by design. Adding a new agent capability means adding a policy entry, not changing code paths. This makes the safety surface auditable: you can answer "what is this agent allowed to do?" by reading config, not source.

The router doesn't transform model outputs. It only decides where the call goes. That separation keeps debugging tractable.

## Stack

Python, FastAPI, Pydantic, async HTTP, multiple LLM provider SDKs (cloud and local), structured JSON logging, GitHub REST/GraphQL APIs for code-side effects, lightweight web UI for the dashboard.

## Status

Private codebase. Sanitized architecture diagram and schemas live in [`docs/architecture.md`](../docs/architecture.md) and the [`examples/`](../examples/) directory.
