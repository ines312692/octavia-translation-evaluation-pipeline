from typing import List

from sacrebleu.metrics import BLEU

from evaluator.models import LengthMetrics, Thresholds


def compute_length_ratios(sources: List[str], translations: List[str]) -> List[float]:
    return [len(t) / len(s) for s, t in zip(sources, translations)]


def compute_length_metrics(ratios: List[float], threshold: float = 1.2) -> LengthMetrics:
    n = len(ratios)
    violations = [r for r in ratios if r > threshold]
    return LengthMetrics(
        average_length_ratio=round(sum(ratios) / n, 4),
        violation_count=len(violations),
        violation_rate=round(len(violations) / n, 4),
        violation_percentage=round(100 * len(violations) / n, 2),
    )


def compute_bleu(sources: List[str], translations: List[str]) -> float:
    bleu = BLEU(effective_order=True)
    result = bleu.corpus_score(translations, [sources])
    return round(result.score, 4)