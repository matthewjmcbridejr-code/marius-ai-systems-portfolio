# Marius Trader

*Paper-only AI trading research cockpit. No live execution — by design.*

A committee-style analysis framework for trade ideas. Multiple agent personas analyze the same setup independently; a judging agent summarizes; the recommendation is logged as a paper outcome and later scored against what actually happened.

## What it does

- Loads a research question as a task (e.g., "evaluate this position over the next N days").
- Runs three persona agents in parallel against the same input:
  - A **bull** agent argues one direction.
  - A **bear** agent argues the other.
  - A **risk** agent flags downside scenarios and tail risk.
- A **judging agent** reads all three views and produces a structured recommendation with explicit confidence and reasoning.
- The recommendation is recorded as a paper trade with a timestamp.
- Later, when real market data arrives, the paper trade is scored against ground truth. Scores accumulate into an evaluation history for the committee.

## What it does not do

There is no broker integration. There is no order-routing code. There is no path — architectural, accidental, or convenient — from "the committee said long" to a real-money position. The system runs on read-only historical data and writes only to a paper log.

This is enforced by the absence of any transport layer to an exchange. Adding one would require a separate review, a separate deployment, and an explicit policy entry — none of which exist or are planned.

## What's interesting

The deliberate non-execution is the architectural feature, not a limitation. The hypothesis is that multi-agent reasoning quality is best studied on a hard task with a clear ground truth, with zero ability to cause real-world harm during the study. Markets meet both criteria.

The committee setup also exposes the value of dissent. Single-model setups discard disagreement; the committee preserves it. A unanimous "long" with high confidence ≠ a split decision the judge resolved as "long with low confidence." The eval history tracks both.

## Stack

Python, LLM provider SDKs (committee can be heterogeneous — different agents can run on different models), structured JSON for paper recommendations, historical market data sources for scoring (read-only), no broker API integration of any kind.

## Status

Research project. Will not become a live trading system without a separate, deliberate review process.
