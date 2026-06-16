"""Human-readable rendering for voice QA reports."""

from __future__ import annotations

from .models import QAReport


def render_text(report: QAReport) -> str:
    lines = [
        "Realtime Voice Agent QA Console",
        f"Call: {report.call_id}",
        f"Score: {report.score}/100",
        f"Status: {report.status}",
        "",
    ]
    for check in report.checks:
        lines.append(f"{check.status.upper()} {check.name}: {check.detail} ({check.points}/{check.max_points})")
        for item in check.evidence[:3]:
            lines.append(f"  - {item}")
    if report.recommendations:
        lines.extend(["", "Recommendations"])
        lines.extend(f"- {note}" for note in report.recommendations)
    return "\n".join(lines)
