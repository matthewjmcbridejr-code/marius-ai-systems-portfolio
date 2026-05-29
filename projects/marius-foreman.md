# Marius Foreman

*Installed missed-call recovery and follow-up system for small home-services contractors.*

Marius Foreman is a done-for-you automation service for contractors who miss calls while they are on jobs. It texts missed callers back, qualifies the lead, alerts the owner, follows up on estimates, and prompts happy customers for reviews — without making the operator run another complicated app.

Public site: [usemarius.com](https://usemarius.com)

Client-facing delivery pages:

- [growth.usemarius.com](https://growth.usemarius.com)
- [nextsteps.usemarius.com](https://nextsteps.usemarius.com)

## What it does

Small home-services businesses — HVAC, plumbing, electrical, roofing, restoration, garage door, pest control — lose jobs when the owner is on a job and cannot answer the phone. The caller hits voicemail, hangs up, and hires the next contractor who responds.

Foreman closes that gap:

1. Detects a missed inbound call or fast hang-up.
2. Sends a fast acknowledgement SMS: “Sorry we missed you — we’re on a job. What do you need help with?”
3. Qualifies the lead through a short SMS flow.
4. Alerts the operator with the qualified job opportunity.
5. Follows up on estimates that have not been accepted.
6. Prompts happy customers for reviews after completion.

The operator does not need a new app, new CRM habit, or complicated dashboard. Foreman installs around the tools and process they already use.

## Commercial direction

Foreman is sold as an installed service, not as a generic self-serve SaaS. The current acquisition path is:

**Free Lead Leak Scan → painful report → $1 missed-call / lead-leak review → paid Foreman install.**

The goal is not to impress contractors with “AI.” The goal is to recover job opportunities they are already paying to generate.

## Approach

The architecture is patterned on the same draft-and-review approach as Marius Mind and McTable: automate low-risk acknowledgement, keep operator visibility around messages that affect customer trust, and maintain proof around what happened.

The core principle: **AI should make the contractor faster, not less accountable.**

## Stack

Python, webhook handlers for call events, SMS provider APIs, GoHighLevel-style CRM and pipeline workflows, calendar integrations, lightweight per-lead state machines, review-prompt scheduling, and operator-facing proof/report pages.

## Status

**Live business** at [usemarius.com](https://usemarius.com). Built as a revenue-first installed service for small home-services contractors.