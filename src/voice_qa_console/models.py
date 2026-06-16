"""Lightweight result models for the voice QA console."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any


@dataclass(frozen=True)
class CheckResult:
    name: str
    status: str
    points: int
    max_points: int
    detail: str
    evidence: list[str] = field(default_factory=list)

    def to_dict(self) -> dict[str, Any]:
        return {
            "name": self.name,
            "status": self.status,
            "points": self.points,
            "max_points": self.max_points,
            "detail": self.detail,
            "evidence": self.evidence,
        }


@dataclass(frozen=True)
class QAReport:
    call_id: str
    score: int
    status: str
    checks: list[CheckResult]
    recommendations: list[str]

    def to_dict(self) -> dict[str, Any]:
        return {
            "call_id": self.call_id,
            "score": self.score,
            "status": self.status,
            "checks": [check.to_dict() for check in self.checks],
            "recommendations": self.recommendations,
        }
