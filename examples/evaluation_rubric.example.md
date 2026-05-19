# Example Evaluation Rubric

A representative rubric used to score outputs for a "document summary" task. This is the format the system stores and applies; the specific weights and criteria are tuned per task type.

---

**Rubric ID:** `rubric_document_summary_v3`
**Task type:** `document_summary`
**Last updated:** 2026-04-12

## Criteria

### Factual Accuracy — weight 0.30

How well the summary preserves the factual content of the source.

| Score | Description |
|---|---|
| 5 | Every factual claim in the summary is supported by the source. No fabricated entities, numbers, or relationships. |
| 4 | All facts present are correct; minor omissions of factual material from the source. |
| 3 | Mostly correct, but one minor fact is mis-stated or mis-attributed. |
| 2 | A material fact is invented or misattributed. |
| 1 | Multiple invented or misattributed facts. |

### Completeness — weight 0.20

How well the summary covers the source's content.

| Score | Description |
|---|---|
| 5 | Every section of the source is represented at an appropriate level of detail. |
| 4 | Minor omissions; the summary's structure still matches the source's. |
| 3 | One significant section is under-represented or missing. |
| 2 | Multiple significant sections missing or compressed past usefulness. |
| 1 | Summary captures less than half the source's substance. |

### Conciseness — weight 0.15

Whether the summary respects the target length without padding.

| Score | Description |
|---|---|
| 5 | Within target length. No filler, no redundancy. |
| 4 | Within target length. Mild redundancy in one or two places. |
| 3 | Slightly over target length, or noticeable filler. |
| 2 | Noticeably over target, or padded to feel longer than necessary. |
| 1 | Significantly over target or padded throughout. |

### Structure — weight 0.15

Whether the summary is organized for the reader.

| Score | Description |
|---|---|
| 5 | Clear sections or paragraphs, easily scannable, logical ordering. |
| 4 | Generally well organized; one transition could be smoother. |
| 3 | Readable but ordering or paragraphing is suboptimal. |
| 2 | Hard to follow. Material jumps around or runs together. |
| 1 | One unbroken wall of text or visibly disorganized. |

### Tone Match — weight 0.10

Whether the summary's register matches the source.

| Score | Description |
|---|---|
| 5 | Tone matches the source's register exactly. |
| 4 | Tone matches with one minor slip. |
| 3 | Tone is broadly appropriate but inconsistent. |
| 2 | Tone clashes with the source (e.g., hype vs. technical, casual vs. formal). |
| 1 | Tone is wrong throughout. |

### No Hallucination — weight 0.10

A specific check beyond Factual Accuracy: zero invented details of any kind (people, places, dates, numbers, claims).

| Score | Description |
|---|---|
| 5 | No invented details. |
| 4 | One borderline detail that is technically extrapolation rather than fabrication. |
| 3 | One clearly invented minor detail. |
| 2 | Multiple invented details. |
| 1 | Invented details pervade the output. |

---

## Computing the Weighted Score

```
weighted_score =
    0.30 * factual_accuracy +
    0.20 * completeness +
    0.15 * conciseness +
    0.15 * structure +
    0.10 * tone_match +
    0.10 * no_hallucination
```

Maximum possible score: 5.0. Minimum: 1.0.

## How Scores Are Used

- Logged with every run alongside the task ID and rubric version.
- Surfaced in the operator dashboard for recent-runs views.
- Compared across rubric versions to track whether changes in prompts, models, or providers improve or regress quality.
- Disagreements between self-evaluated scores and human-reviewed scores are flagged for rubric calibration.

## When Rubrics Change

Each rubric is versioned. A change in any criterion definition, weight, or scoring guide increments the version. Historical scores stay attached to the rubric version under which they were produced, so version-over-version comparisons remain meaningful.

Rubric changes are reviewed in their own pull requests, not bundled with code changes.
