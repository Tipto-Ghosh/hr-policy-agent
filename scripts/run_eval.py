from __future__ import annotations

import argparse
import sys
from pathlib import Path

from hr_agent.evaluation import evaluate_retrieval, load_golden_examples


def _build_real_retrieve_fn():
    """
    Wires up the real Pinecone-backed retriever via the project's
    settings-driven helper. Kept separate from `evaluate_retrieval` so
    the scoring logic itself has no hard dependency on Pinecone /
    embeddings being installed or configured.
    """
    from hr_agent.retrieval import get_retriever

    retriever = get_retriever()

    def retrieve_fn(question: str, k: int):
        return retriever.invoke(question)[:k]

    return retrieve_fn


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--k", type=int, default=5, help="top-k to retrieve")
    parser.add_argument(
        "--dataset",
        type=Path,
        default=Path("data/eval/golden_dev.jsonl"),
        help="path to golden JSONL dataset",
    )
    args = parser.parse_args()

    if not args.dataset.exists():
        print(f"Dataset not found: {args.dataset}", file=sys.stderr)
        print(
            "Create data/eval/golden_dev.jsonl with one JSON object per line: "
            '{"question": "...", "expected_breadcrumb_contains": "..."}',
            file=sys.stderr,
        )
        sys.exit(1)

    examples = load_golden_examples(args.dataset)
    if not examples:
        print(f"No examples found in {args.dataset}", file=sys.stderr)
        sys.exit(1)

    retrieve_fn = _build_real_retrieve_fn()
    report = evaluate_retrieval(examples, retrieve_fn, k=args.k)
    report.print_report()


if __name__ == "__main__":
    main()