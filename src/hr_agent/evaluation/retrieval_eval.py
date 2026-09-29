from __future__ import annotations

import json
from pathlib import Path
from typing import Callable

from hr_agent.evaluation.models import EvalReport, EvalResult, GoldenExample, RetrievedDoc

__all__ = [
    "load_golden_examples",
    "evaluate_retrieval",
]

def load_golden_examples(path: Path) -> list[GoldenExample]:
    """
    Read a JSONL golden dataset. Raises ValueError with line number on
    invalid JSON so bad hand-edits are easy to locate.
    """
    examples: list[GoldenExample] = []
    with open(path, "r", encoding="utf-8") as f:
        for line_num, line in enumerate(f, start=1):
            line = line.strip()
            if not line:
                continue
            try:
                raw = json.loads(line)
            except json.JSONDecodeError as e:
                raise ValueError(f"{path}:{line_num}: invalid JSON - {e}") from e
            examples.append(
                GoldenExample(
                    question=raw["question"],
                    expected_breadcrumb_contains=raw["expected_breadcrumb_contains"],
                )
            )
    return examples

def evaluate_retrieval(
    examples: list[GoldenExample],
    retrieve_fn: Callable[[str, int], list[RetrievedDoc]],
    k: int,
) -> EvalReport:
    """
    Core evaluation logic, decoupled from the retriever's real construction
    so it can be unit-tested with a fake `retrieve_fn`.

    `retrieve_fn(question, k) -> list[doc]` -> a thin wrapper around whatever
    the real retriever exposes (e.g. `lambda q, k: retriever.invoke(q)[:k]`).
    """
    report = EvalReport(k=k)
    for example in examples:
        docs = retrieve_fn(example.question, k)
        breadcrumbs = [d.metadata.get("breadcrumb", "") for d in docs]
        expected_lower = example.expected_breadcrumb_contains.lower()
        hit = any(expected_lower in b.lower() for b in breadcrumbs if b)
        report.results.append(
            EvalResult(
                question=example.question,
                expected_breadcrumb_contains=example.expected_breadcrumb_contains,
                hit=hit,
                retrieved_breadcrumbs=breadcrumbs,
            )
        )
    return report