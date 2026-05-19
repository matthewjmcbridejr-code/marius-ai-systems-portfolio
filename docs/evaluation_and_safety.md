# Evaluation and Safety

How outputs are scored and how the system is kept safe to run.

---

## Safety Principles

These are the non-negotiable rules the system is built around. They are stated up front so reviewers can confirm they are enforced.

### 1. No secrets in agent-accessible context

API keys, tokens, and credentials never appear in prompts or responses. They are injected at the network boundary by the gateway, scoped to a single request, and stripped from logs.

If an agent's reasoning trace surfaces a value that looks like a key, the log writer redacts it before persistence.

### 2. No live trading

The trading-research cockpit is a research surface only. It does not have broker credentials, does not have an order-placement code path, and does not have any operational route that touches a real market account. Paper outcomes are scored against historical data, not used to drive live execution.

This is enforced architecturally: the relevant module simply has no transport layer to an exchange. If the operator wanted to add one, it would require a separate review and a separate deployment.

### 3. No autonomous destructive Git actions

Agents can read repositories, propose changes, and open pull requests. Agents cannot:

- Force-push to any branch.
- Delete branches.
- Rewrite history.
- Merge their own pull requests.
- Push directly to a protected branch.

These are enforced by repository settings (branch protection rules), by the agent's GitHub token scope, and by the policy layer rejecting any task whose intended action falls into one of these categories.

### 4. Human-reviewed pull requests for code changes

Any code change reaches the main branch through a PR opened by an agent and merged by a human. The PR template requires:

- The task ID that produced the change.
- A short rationale.
- The relevant rubric scores.
- A note on side effects (e.g., "modifies migration files," "changes API contract").

Reviewers are expected to read the diff, not rubber-stamp.

### 5. Structured proof bundles

Before an agent proposes a change, it assembles a proof bundle: the files it read, the lines it cited, the searches it ran, and the reasoning that led to the proposal. The bundle is referenced from the PR and is queryable from the dashboard.

This is what makes the system auditable. A reviewer can answer "why did the agent want to do this?" without re-running the task.

---

## Evaluation Rubric Design

Outputs are scored against task-specific rubrics. A rubric is a small set of named criteria, each with a 1–5 scoring guide and a relative weight.

### Example rubric criteria (for a "summarize this document" task)

| Criterion | Weight | What 5 looks like | What 1 looks like |
|---|---|---|---|
| Factual accuracy | 0.30 | No invented facts. All claims traceable to the source. | Multiple invented facts or misattributions. |
| Completeness | 0.20 | Captures every section the source covers. | Major sections of the source are missing. |
| Conciseness | 0.15 | Within target length, no padding. | Significantly over length or padded with filler. |
| Structure | 0.15 | Clear sections, scannable. | One wall of text or random ordering. |
| Tone match | 0.10 | Matches the source's register. | Tone clashes with source (e.g., hype vs. technical). |
| No hallucination | 0.10 | Zero invented details. | Multiple invented details. |

The weighted average becomes the task's score for that run.

### How rubrics are used

- A new rubric is drafted when a task type is first introduced.
- Each task references its rubric by ID.
- Every run is scored, and the score is logged alongside the run.
- Rubrics evolve based on observed failure modes. Changes are versioned.

### Self-evaluation vs. human evaluation

Some scores are computed by a separate LLM judging the primary LLM's output. These are useful for fast feedback but not authoritative. A subset of runs is also scored by a human, and the human scores are the ground truth used to calibrate the judge.

When the judge and the human disagree, that disagreement is a signal — usually about the rubric itself.

---

## Logging

Every run produces a structured log entry with at minimum:

```
{
  "task_id": "task_...",
  "task_type": "...",
  "model_provider": "...",
  "model_id": "...",
  "started_at": "...",
  "completed_at": "...",
  "token_usage": { "input": ..., "output": ... },
  "rubric_id": "...",
  "rubric_scores": { "criterion": 0..5, ... },
  "weighted_score": 0..5,
  "outcome": "completed" | "failed" | "cancelled",
  "side_effects": [ ... ],
  "proof_bundle_id": "..."
}
```

Logs are append-only. They are not used to store the model's raw output; the output is stored separately and referenced by ID.

---

## What This Section Does Not Cover

- Specific log schemas in production code.
- Specific repository names or branch protection rule IDs.
- Specific provider account configurations.
- Threat-model documentation for adversarial inputs (handled separately, not public).
