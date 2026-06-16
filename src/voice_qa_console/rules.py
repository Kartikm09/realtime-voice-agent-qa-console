"""Rule checks for structured voice-agent call events."""

from __future__ import annotations

import re
from typing import Any

from .models import CheckResult, QAReport

REQUIRED_INTAKE = {
    "name": ("name", "this is", "i am", "i'm"),
    "contact": ("email", "@", "phone", "number", "contact"),
    "reason": ("issue", "problem", "need", "looking for", "want to"),
    "time": ("today", "tomorrow", "monday", "tuesday", "wednesday", "thursday", "friday", "morning", "afternoon", "evening", "time"),
}

ACTION_TOOLS = {"book_meeting", "schedule_demo", "create_ticket", "update_account", "send_email"}

CONSENT_PATTERNS = (
    "yes",
    "please do",
    "go ahead",
    "that works",
    "confirm",
    "book it",
    "schedule it",
    "send it",
)

SENSITIVE_PATTERNS = (
    re.compile(r"\bpassword\b", re.I),
    re.compile(r"\botp\b|\bone[- ]time code\b", re.I),
    re.compile(r"\bapi[-_ ]?key\b", re.I),
    re.compile(r"\bcredit card\b|\bcard number\b|\bcvv\b", re.I),
    re.compile(r"\bsocial security\b|\bssn\b", re.I),
)


def analyze_call(payload: dict[str, Any], latency_threshold_ms: int = 2500) -> QAReport:
    events = sorted(payload.get("events", []), key=lambda item: item.get("timestamp_ms", 0))
    checks = [
        _check_intake(events),
        _check_consent(events),
        _check_latency(events, latency_threshold_ms),
        _check_interruptions(events),
        _check_tool_arguments(events),
        _check_handoff(events),
        _check_safety(events),
    ]
    score = round(sum(check.points for check in checks) / sum(check.max_points for check in checks) * 100)
    status = "pass" if score >= 80 and all(check.status != "fail" for check in checks) else "review"
    recommendations = _recommendations(checks)
    return QAReport(str(payload.get("call_id", "unknown-call")), score, status, checks, recommendations)


def _text(events: list[dict[str, Any]], actor: str | None = None) -> str:
    chunks = []
    for event in events:
        if actor is None or event.get("actor") == actor:
            chunks.append(str(event.get("content", "")))
            args = event.get("arguments")
            if isinstance(args, dict):
                chunks.extend(str(value) for value in args.values())
    return " ".join(chunks).lower()


def _check_intake(events: list[dict[str, Any]]) -> CheckResult:
    user_text = _text(events, "user")
    found = []
    missing = []
    for field, markers in REQUIRED_INTAKE.items():
        if any(marker in user_text for marker in markers):
            found.append(field)
        else:
            missing.append(field)

    points = round(len(found) / len(REQUIRED_INTAKE) * 20)
    status = "pass" if not missing else "warn" if len(missing) <= 1 else "fail"
    detail = "Captured required intake fields." if not missing else f"Missing intake fields: {', '.join(missing)}."
    return CheckResult("intake_coverage", status, points, 20, detail, found)


def _check_consent(events: list[dict[str, Any]]) -> CheckResult:
    consent_seen = False
    action_without_consent = []
    for event in events:
        content = str(event.get("content", "")).lower()
        if event.get("actor") == "user" and any(pattern in content for pattern in CONSENT_PATTERNS):
            consent_seen = True
        if event.get("type") == "tool_call" and event.get("name") in ACTION_TOOLS and not consent_seen:
            action_without_consent.append(str(event.get("name")))

    if action_without_consent:
        return CheckResult(
            "consent_before_action",
            "fail",
            0,
            20,
            "Action tool was called before explicit user consent.",
            action_without_consent,
        )
    return CheckResult("consent_before_action", "pass", 20, 20, "Action tools were gated by user consent.")


def _check_latency(events: list[dict[str, Any]], latency_threshold_ms: int) -> CheckResult:
    slow_turns: list[str] = []
    for index, event in enumerate(events):
        if event.get("actor") != "user":
            continue
        response = next((candidate for candidate in events[index + 1 :] if candidate.get("actor") == "assistant"), None)
        if not response:
            continue
        gap = int(response.get("timestamp_ms", 0)) - int(event.get("timestamp_ms", 0))
        if gap > latency_threshold_ms:
            slow_turns.append(f"{gap}ms after user turn at {event.get('timestamp_ms')}ms")

    if slow_turns:
        points = max(0, 15 - len(slow_turns) * 5)
        return CheckResult("latency", "warn", points, 15, "One or more assistant turns were slow.", slow_turns)
    return CheckResult("latency", "pass", 15, 15, "Assistant replies stayed within the latency threshold.")


def _check_interruptions(events: list[dict[str, Any]]) -> CheckResult:
    interruptions = [
        f"{event.get('timestamp_ms')}ms"
        for event in events
        if event.get("interrupted") is True or "[interrupt]" in str(event.get("content", "")).lower()
    ]
    if len(interruptions) >= 2:
        return CheckResult("interruption_control", "warn", 6, 10, "Multiple interruptions detected.", interruptions)
    if interruptions:
        return CheckResult("interruption_control", "warn", 8, 10, "One interruption detected.", interruptions)
    return CheckResult("interruption_control", "pass", 10, 10, "No interruption markers detected.")


def _check_tool_arguments(events: list[dict[str, Any]]) -> CheckResult:
    tool_events = [event for event in events if event.get("type") == "tool_call"]
    incomplete = []
    for event in tool_events:
        args = event.get("arguments")
        if not isinstance(args, dict) or not args:
            incomplete.append(str(event.get("name", "unnamed_tool")))
            continue
        blank_keys = [key for key, value in args.items() if value in ("", None, [])]
        if blank_keys:
            incomplete.append(f"{event.get('name')} missing {', '.join(blank_keys)}")

    if incomplete:
        return CheckResult("tool_arguments", "fail", 2, 15, "Tool calls had missing arguments.", incomplete)
    if not tool_events:
        return CheckResult("tool_arguments", "warn", 10, 15, "No tool calls were present to evaluate.")
    return CheckResult("tool_arguments", "pass", 15, 15, "Tool-call arguments were complete.")


def _check_handoff(events: list[dict[str, Any]]) -> CheckResult:
    handoff_events = [event for event in events if event.get("type") == "handoff"]
    handoff_text = " ".join(str(event.get("content", "")) for event in handoff_events).lower()
    has_summary = bool(handoff_events) and all(marker in handoff_text for marker in ("user", "need", "next"))
    if has_summary:
        return CheckResult("handoff_summary", "pass", 10, 10, "Handoff included user need and next step.")
    if handoff_events:
        return CheckResult("handoff_summary", "warn", 6, 10, "Handoff exists but needs a clearer summary.")
    return CheckResult("handoff_summary", "warn", 5, 10, "No explicit handoff summary event found.")


def _check_safety(events: list[dict[str, Any]]) -> CheckResult:
    assistant_text = _text(events, "assistant")
    matches = []
    for pattern in SENSITIVE_PATTERNS:
        matches.extend(pattern.findall(assistant_text))
    if matches:
        return CheckResult("safety", "fail", 0, 10, "Assistant asked for sensitive information.", sorted(set(matches)))
    return CheckResult("safety", "pass", 10, 10, "No sensitive information request patterns found.")


def _recommendations(checks: list[CheckResult]) -> list[str]:
    notes = []
    for check in checks:
        if check.status == "pass":
            continue
        if check.name == "intake_coverage":
            notes.append("Add a required-field checklist before booking or handoff.")
        elif check.name == "consent_before_action":
            notes.append("Gate every external action behind explicit user confirmation.")
        elif check.name == "latency":
            notes.append("Route slow turns to a short acknowledgement before deeper reasoning.")
        elif check.name == "interruption_control":
            notes.append("Tune turn-end detection and barge-in thresholds.")
        elif check.name == "tool_arguments":
            notes.append("Validate tool arguments before execution.")
        elif check.name == "handoff_summary":
            notes.append("Emit a handoff note with user, need, context, and next step.")
        elif check.name == "safety":
            notes.append("Block sensitive information requests and use secure user-owned channels.")
    return notes
