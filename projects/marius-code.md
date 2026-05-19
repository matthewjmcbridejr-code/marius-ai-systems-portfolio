# Marius Code

*Code-reading and PR-proposing agent.*

A code-focused agent that reads a repository, identifies the files relevant to a task, drafts a change, and ships it as a pull request a human reviews and merges.

## What it does

Given a clear spec ("update X to handle Y," "refactor Z to use the new API," "fix the bug in module W"), the agent:

1. Walks the repository to identify relevant files using structural parsing and semantic search.
2. Reads them in full.
3. Produces a diff against a feature branch.
4. Opens a pull request with a structured description: task ID, files read, lines cited, proposed change, rubric scores.
5. Stops. A human merges or closes the PR.

The agent does not push to `main`, does not merge its own PRs, does not force-push, does not delete branches, does not rewrite history. These are enforced by token scope, branch protection rules, and the policy layer.

## Approach

Most "code agents" treat the repository as a black box and ask the LLM to invent fixes. Marius Code inverts that: the repository is the source of truth, and the LLM proposes edits against what's actually there.

The proof bundle attached to every PR makes the agent's reasoning legible without making it authoritative. A reviewer can see which files the agent read, which lines it cited, and which alternatives it considered before settling on the proposed diff — and disagree.

## Architecture

- Tree-sitter (or similar) for structural parsing across multiple languages.
- Vector search for semantic locality when a spec doesn't name files directly.
- LLM provider abstraction inherited from Marius Mind — same routing, same policy, same logging.
- GitHub API for branch creation, commit, PR opening, and read of review status.
- Strict input/output validation on the proposed diff before opening the PR.

## What's interesting

The boring design choices are the point. No autonomous merge. No "the agent will figure it out." No prompt that says "you are an expert engineer." The trick is making the agent's work auditable enough that a reviewer can trust the diff after a 30-second scan, not after rereading the whole file.

## Stack

Python, GitHub REST and GraphQL APIs, tree-sitter, vector store for code embeddings, the Marius Mind provider abstraction.

## Status

Private codebase. Built and operated on this user's own repositories. Designed so the same pattern could host external work safely.
