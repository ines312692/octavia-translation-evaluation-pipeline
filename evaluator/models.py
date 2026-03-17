from dataclasses import dataclass, field
from typing import Dict, List


@dataclass(frozen=True)
class SegmentResult:
    index: int
    source: str
    translation: str
    length_ratio: float
    exceeds_threshold: bool


@dataclass(frozen=True)
class LengthMetrics:
    average_length_ratio: float
    violation_count: int
    violation_rate: float
    violation_percentage: float


@dataclass(frozen=True)
class Thresholds:
    max_average_length_ratio: float = 1.2
    max_violation_percentage: float = 10.0
    min_bleu_score: float = 25.0

    @classmethod
    def from_dict(cls, data: Dict[str, float]) -> "Thresholds":
        return cls(
            max_average_length_ratio=data.get("max_average_length_ratio", 1.2),
            max_violation_percentage=data.get("max_violation_percentage", 10.0),
            min_bleu_score=data.get("min_bleu_score", 25.0),
        )

    def to_dict(self) -> Dict[str, float]:
        return {
            "max_average_length_ratio": self.max_average_length_ratio,
            "max_violation_percentage": self.max_violation_percentage,
            "min_bleu_score": self.min_bleu_score,
        }


@dataclass(frozen=True)
class CheckResults:
    avg_length_ratio_ok: bool
    violation_rate_ok: bool
    bleu_ok: bool

    @property
    def all_passed(self) -> bool:
        return self.avg_length_ratio_ok and self.violation_rate_ok and self.bleu_ok

    def to_dict(self) -> Dict[str, bool]:
        return {
            "avg_length_ratio_ok": self.avg_length_ratio_ok,
            "violation_rate_ok": self.violation_rate_ok,
            "bleu_ok": self.bleu_ok,
        }


@dataclass(frozen=True)
class EvaluationResult:
    length_metrics: LengthMetrics
    bleu_score: float
    thresholds: Thresholds
    checks: CheckResults
    segments: List[SegmentResult]

    @property
    def decision(self) -> str:
        return "PASS" if self.checks.all_passed else "FAIL"

    @property
    def passed(self) -> bool:
        return self.checks.all_passed