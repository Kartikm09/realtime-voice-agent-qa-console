---
name: voice-agent-qa
description: Evaluate structured voice-agent or phone-assistant call event logs for intake coverage, consent before action, latency, interruption handling, tool-call arguments, handoff quality, and sensitive-data safety.
---

# Voice Agent QA

Use this skill when reviewing a voice-agent call transcript, event log, or synthetic voice workflow.

## Workflow

1. Load the event log as structured JSON when available.
2. Check whether the assistant collected name, contact, user need, and timing.
3. Verify that booking, ticket creation, email sending, or account updates happened only after explicit user consent.
4. Inspect response timing between user turns and assistant turns.
5. Look for interruption markers or obvious turn-taking problems.
6. Validate that tool calls have complete arguments.
7. Confirm that any handoff includes user, need, context, and next step.
8. Flag requests for passwords, OTPs, API keys, card details, or other sensitive information.

## Output

Return a scorecard with pass, warn, or fail for each category, then list the highest-impact fixes first.
