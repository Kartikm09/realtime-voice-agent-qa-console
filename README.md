# Realtime Voice Agent QA Console

Realtime-style QA scorecards for voice agents, phone assistants, and Vapi-like call workflows.

This repository turns call event logs into practical QA reports for:

- Intake completeness
- Consent before booking or account actions
- Response latency
- Interruption and turn-taking quality
- Tool-call argument quality
- Handoff readiness
- Unsafe information requests

The examples are synthetic and public-safe, so the project can be used as a portfolio artifact without exposing client data.

## Why It Exists

Voice agents are moving from demos into operational workflows. The risky part is not only speech quality; it is whether the assistant collects the right details, asks before taking action, avoids sensitive requests, and leaves a clean handoff trail.

This console gives a lightweight way to evaluate those behaviors from structured call events.

## Quick Start

```bash
PYTHONPATH=src python3 -m voice_qa_console.cli analyze examples/call_events.json
```

JSON output:

```bash
PYTHONPATH=src python3 -m voice_qa_console.cli analyze examples/call_events.json --format json
```

Run tests:

```bash
PYTHONPATH=src python3 -m unittest discover -s tests
```

## Example Output

```text
Realtime Voice Agent QA Console
Score: 87/100
Status: pass

PASS intake_coverage
PASS consent_before_action
PASS latency
WARN interruption_control
PASS tool_arguments
PASS handoff_summary
PASS safety
```

## Input Format

The analyzer expects a JSON file with a top-level `events` array:

```json
{
  "call_id": "demo-001",
  "events": [
    {"timestamp_ms": 0, "actor": "assistant", "type": "message", "content": "Thanks for calling. May I ask your name?"},
    {"timestamp_ms": 1300, "actor": "user", "type": "message", "content": "This is Asha."}
  ]
}
```

Supported event fields:

- `timestamp_ms`
- `actor`: `assistant`, `user`, `tool`, or `system`
- `type`: `message`, `tool_call`, `handoff`, or `note`
- `content`
- `name` for tool calls
- `arguments` for tool-call payloads
- `interrupted` when a turn was interrupted

## Portfolio Signal

This project demonstrates:

- Voice-agent QA
- AI tool-use evaluation
- Synthetic evaluation data design
- Rubric-based scoring
- Python CLI development
- Public-safe AI training portfolio work

## Public-Safe Note

This project avoids client names, model vendor names, private transcripts, and production secrets. All call events are synthetic.

## Synthetic event coverage and limitations

The analyzer accepts `silence` events with `duration_ms`, `capture_error` and
`stalled` events, in addition to interruption and handoff events. Silence of at
least 5000 ms warns; capture errors and explicit stalls fail capture health. An
unanswered user turn now warns instead of silently passing latency.

Consent is a conservative transcript hint: an entire affirmative utterance,
used once within 30 seconds and reset by another user utterance. It is not
proof of exact-action authorization. A live integration must bind an approval
to the full proposed action; the separate durable runner in
[Agentic Eval Ops Kit](https://github.com/Kartikm09/agentic-eval-ops-kit) demonstrates
that local synthetic contract. No real provider, microphone, audio capture,
calendar booking or handoff integration was tested. Timing here comes from
synthetic event timestamps, not actual provider latency. Existing text safety
checks are keyword heuristics and require reviewer judgment.

Reproduce all regression and example checks with
`PYTHONPATH=src python3 -m unittest discover -s tests -v`.
