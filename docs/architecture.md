# Architecture

A sanitized description of the architectural pattern used in the Marius AI Systems Platform.

This document describes the **shape** of the system. Specific implementation files, internal route paths, environment variable names, and provider account identifiers are intentionally omitted.

---

## High-Level Components

```
                ┌──────────────────────────┐
                │   Operator Dashboard     │
                │   (read-only views,      │
                │    approval queue)       │
                └─────────────┬────────────┘
                              │
┌─────────────────────────────┴───────────────────────────────┐
│                    FastAPI Gateway                          │
│   - Auth, request validation, rate limiting                 │
│   - Routes requests to internal services                    │
└──────┬──────────────────┬──────────────┬────────────────────┘
       │                  │              │
       ▼                  ▼              ▼
┌─────────────┐  ┌─────────────────┐  ┌──────────────────┐
│  Provider   │  │  Policy Layer   │  │  Task            │
│  Routing    │  │  (allow / deny  │  │  Coordination    │
│  (OpenAI,   │  │   / require     │  │  (queue, state,  │
│   Anthropic,│  │   approval)     │  │   retries)       │
│   local,    │  │                 │  │                  │
│   etc.)     │  │                 │  │                  │
└─────────────┘  └─────────────────┘  └──────────────────┘
       │                  │                    │
       └──────────────────┴────────────────────┘
                          │
                          ▼
              ┌───────────────────────┐
              │  Evaluation & Logging │
              │  (rubric scoring,     │
              │   structured logs,    │
              │   audit trail)        │
              └───────────────────────┘
                          │
                          ▼
              ┌───────────────────────┐
              │  GitHub PR Workflow   │
              │  (proposed changes    │
              │   ship as PRs with    │
              │   human review)       │
              └───────────────────────┘
```

---

## Component Roles

### FastAPI Gateway

A small Python service that owns the public-facing HTTP surface.

- Validates request shape using Pydantic models.
- Authenticates callers (token-based) and applies per-route rate limits.
- Forwards validated requests to internal services rather than exposing them directly.
- Returns structured JSON, never raw model output without metadata.

This layer is deliberately thin. Business logic lives downstream.

### Provider Routing

A small abstraction over LLM providers (cloud and local). The routing layer decides which model handles a given task based on:

- Task type (e.g., short classification vs. long generation vs. tool use)
- Cost ceiling for the calling workflow
- Provider availability and recent error rates
- An explicit override if the operator pins a specific model

The router does not transform the actual model output — it picks the endpoint and forwards.

### Policy Layer

Before an agent action takes effect, the policy layer evaluates it against a set of rules:

- **Allow:** action runs immediately and is logged.
- **Require approval:** action is queued for a human reviewer in the dashboard.
- **Deny:** action is rejected with a structured reason, written to the audit log.

Rules are declarative (think YAML/JSON config), not hard-coded. The default for unfamiliar actions is "require approval," not "allow."

### Task Coordination

Multi-step agent workflows are modeled as tasks with explicit state:

- `queued` → `running` → `awaiting_review` → `completed` / `failed` / `cancelled`

A task carries its prompt history, the artifacts it has produced, and a proof bundle (the structured evidence the agent gathered before proposing a change). Restarts are idempotent: a re-run from a checkpoint must not duplicate side effects.

### Evaluation & Logging

Every model call is logged as a structured record:

- input shape (sanitized — no PII)
- model and provider
- token usage and latency
- output shape and any tool calls produced
- evaluation scores against the relevant rubric

Logs are append-only and stored separately from the model output itself, so eval data can be queried without re-reading payloads.

### Dashboard / Operator View

A read-mostly web view giving the operator:

- A live feed of in-progress tasks
- An approval queue for actions blocked by the policy layer
- Recent evaluation scores, grouped by task type
- Quick links to the underlying PRs and logs

The dashboard does not run agent actions directly. It only displays state and lets the operator approve / reject items the policy layer has flagged.

### GitHub PR Workflow

When an agent proposes a change to a code repository, it does so as a pull request, not a direct push.

- The agent commits to a branch.
- The PR description includes the task ID, the rubric scores, and a short rationale.
- A human reviews the diff and merges (or closes) the PR.
- The merge event closes the loop back to the task coordinator.

Destructive Git actions (force-push, branch deletion, history rewrites) are not permitted from any agent path.

### Human Approval Gate

The combination of the policy layer, dashboard approval queue, and GitHub PR workflow forms a single conceptual gate: **a human reviews and authorizes anything the system has not been explicitly pre-cleared to do.**

This is a design choice. It is slower than full autonomy. It is also what makes the system safe enough to run.

---

## What This Architecture Optimizes For

- **Reviewability.** Every action leaves a trace a human can read.
- **Provider portability.** Swapping a model is a config change, not a rewrite.
- **Evaluation feedback.** Scores attach to runs, so version-over-version comparison is cheap.
- **Slow, deliberate writes.** Reads and analyses run freely; writes go through gates.

## What This Architecture Does Not Try To Do

- Maximize throughput at the cost of review.
- Operate fully autonomously without human supervision.
- Hide its reasoning from the operator.
