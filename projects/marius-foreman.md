# Marius Foreman

*Missed-call recovery system for small home-services contractors.*

A done-for-you automation that texts missed callers back, qualifies the lead, alerts the owner, follows up on estimates, and prompts happy customers for reviews — without making the operator run another complicated app.

## What it does

Small home-services businesses — HVAC, plumbing, electrical, roofing — lose meaningful revenue to missed calls. The operator is on a job. The phone rings. The caller goes to voicemail. The caller hangs up. The caller hires the next vendor that picks up.

Foreman closes that gap:

1. Detects a missed inbound call (or a fast hang-up).
2. Sends a context-aware SMS within ~30 seconds: "Sorry we missed you — we're on a job. What's the issue?"
3. Qualifies the lead through a short SMS flow.
4. Pings the operator's phone with the qualified lead so they can decide whether to call back, schedule, or pass.
5. Follows up if the operator sent an estimate that hasn't been accepted.
6. After job completion, prompts the customer for a Google or platform review.

The operator doesn't change their phone, their calendar, or their job-management tool. Foreman installs against what they already use.

## Approach

The architecture is patterned on the same draft-and-review approach as Marius Mind: **agents propose, humans approve before any outbound communication reaches a customer**. The qualification SMS is sent automatically because it's a low-stakes acknowledgement. The estimate follow-up and review request are queued for the operator's quick approval — they read it, tap accept, it sends.

This avoids the failure mode of automated outbound systems where an AI-generated message reaches a customer the operator wouldn't have wanted to contact.

## Stack

Python, webhook handlers for call events, SMS provider APIs (carrier-agnostic), calendar APIs, lightweight per-lead state machines, simple review-prompt scheduler.

## Status

**Live business** at [usemarius.com](https://usemarius.com). Sold as an installed service to small home-services contractors, not as a self-serve app.
