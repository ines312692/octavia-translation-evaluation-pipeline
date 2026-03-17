from evaluator.models import CheckResults, LengthMetrics, Thresholds

DEFAULT_THRESHOLDS = Thresholds()


def evaluate_pass_fail(
    length_metrics: LengthMetrics,
    bleu_score: float,
    thresholds: Thresholds = DEFAULT_THRESHOLDS,
) -> CheckResults:
    return CheckResults(
        avg_length_ratio_ok=length_metrics.average_length_ratio <= thresholds.max_average_length_ratio,
        violation_rate_ok=length_metrics.violation_percentage <= thresholds.max_violation_percentage,
        bleu_ok=bleu_score >= thresholds.min_bleu_score,
    )