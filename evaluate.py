import argparse
import json
import logging
import sys
from pathlib import Path

from evaluator.loader import load_segments
from evaluator.metrics import compute_bleu, compute_length_metrics, compute_length_ratios
from evaluator.models import EvaluationResult, Thresholds
from evaluator.reporter import build_segment_results, print_summary, result_to_dict, save_report
from evaluator.thresholds import DEFAULT_THRESHOLDS, evaluate_pass_fail

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
    datefmt="%Y-%m-%dT%H:%M:%S",
)
logger = logging.getLogger(__name__)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Octavia Translation Evaluation Pipeline",
        formatter_class=argparse.ArgumentDefaultsHelpFormatter,
    )
    parser.add_argument("--source", default="data/source.txt", help="Path to source text file")
    parser.add_argument("--translation", default="data/translation.txt", help="Path to translated text file")
    parser.add_argument("--output", default="reports/report.json", help="Path for the output JSON report")
    parser.add_argument("--config", default=None, help="Path to JSON thresholds config file")
    parser.add_argument("--lang-pair", default="en-es", help="Language pair identifier (e.g. en-es, en-fr)")
    return parser.parse_args()


def load_thresholds(config_path: str | None) -> Thresholds:
    if config_path is None:
        return DEFAULT_THRESHOLDS
    path = Path(config_path)
    if not path.exists():
        logger.warning("Config file not found: %s — using defaults", config_path)
        return DEFAULT_THRESHOLDS
    with path.open(encoding="utf-8") as f:
        data = json.load(f)
    thresholds = Thresholds.from_dict(data)
    logger.info("Thresholds loaded from %s", config_path)
    return thresholds


def main() -> int:
    args = parse_args()
    thresholds = load_thresholds(args.config)

    logger.info("Loading source segments from: %s", args.source)
    sources = load_segments(args.source)

    logger.info("Loading translation segments from: %s", args.translation)
    translations = load_segments(args.translation)

    if len(sources) != len(translations):
        logger.error(
            "Segment count mismatch: %d source vs %d translation",
            len(sources),
            len(translations),
        )
        return 1

    logger.info("Computing length ratios")
    ratios = compute_length_ratios(sources, translations)
    length_metrics = compute_length_metrics(ratios, threshold=thresholds.max_average_length_ratio)

    logger.info("Computing BLEU score")
    bleu_score = compute_bleu(sources, translations)

    logger.info("Evaluating pass/fail verdict")
    checks = evaluate_pass_fail(length_metrics, bleu_score, thresholds)

    segments = build_segment_results(
        sources, translations, ratios, thresholds.max_average_length_ratio
    )

    result = EvaluationResult(
        length_metrics=length_metrics,
        bleu_score=bleu_score,
        thresholds=thresholds,
        checks=checks,
        segments=segments,
    )

    payload = result_to_dict(result, lang_pair=args.lang_pair)
    save_report(payload, args.output)
    print_summary(payload)

    return 0 if result.passed else 1


if __name__ == "__main__":
    sys.exit(main())