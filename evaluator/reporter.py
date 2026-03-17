import json
import logging
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List

from evaluator.models import EvaluationResult, SegmentResult

logger = logging.getLogger(__name__)


def build_segment_results(
    sources: List[str],
    translations: List[str],
    ratios: List[float],
    threshold: float,
) -> List[SegmentResult]:
    return [
        SegmentResult(
            index=i + 1,
            source=s,
            translation=t,
            length_ratio=round(r, 4),
            exceeds_threshold=r > threshold,
        )
        for i, (s, t, r) in enumerate(zip(sources, translations, ratios))
    ]


def result_to_dict(result: EvaluationResult, lang_pair: str) -> Dict[str, Any]:
    return {
        "pipeline": "Octavia Translation Evaluation Pipeline",
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "language_pair": lang_pair,
        "summary": {
            "total_segments": len(result.segments),
            "average_length_ratio": result.length_metrics.average_length_ratio,
            "violation_count": result.length_metrics.violation_count,
            "violation_percentage": result.length_metrics.violation_percentage,
            "bleu_score": result.bleu_score,
            "decision": result.decision,
        },
        "thresholds": result.thresholds.to_dict(),
        "checks": result.checks.to_dict(),
        "segments": [
            {
                "index": seg.index,
                "source": seg.source,
                "translation": seg.translation,
                "length_ratio": seg.length_ratio,
                "exceeds_threshold": seg.exceeds_threshold,
            }
            for seg in result.segments
        ],
    }


def save_report(payload: Dict[str, Any], output_path: str) -> None:
    path = Path(output_path)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2, ensure_ascii=False), encoding="utf-8")
    logger.info("Report saved to %s", path)


def print_summary(payload: Dict[str, Any]) -> None:
    s = payload["summary"]
    checks = payload["checks"]
    decision = s["decision"]
    sep = "=" * 60

    print(sep)
    print("  Octavia Translation Evaluation Pipeline")
    print(sep)
    print(f"  Language pair           : {payload['language_pair']}")
    print(f"  Generated at            : {payload['generated_at']}")
    print(sep)
    print(f"  Segments evaluated      : {s['total_segments']}")
    print(f"  Average length ratio    : {s['average_length_ratio']}")
    print(f"  Length violations       : {s['violation_count']} ({s['violation_percentage']}%)")
    print(f"  BLEU score              : {s['bleu_score']}")
    print(sep)
    print("  CHECK RESULTS")
    print(f"  avg_length_ratio_ok     : {'PASS' if checks['avg_length_ratio_ok'] else 'FAIL'}")
    print(f"  violation_rate_ok       : {'PASS' if checks['violation_rate_ok'] else 'FAIL'}")
    print(f"  bleu_ok                 : {'PASS' if checks['bleu_ok'] else 'FAIL'}")
    print(sep)
    print(f"  FINAL DECISION: {decision}")
    print(sep)