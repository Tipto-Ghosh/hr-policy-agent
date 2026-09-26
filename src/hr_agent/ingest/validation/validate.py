# src/hr_agent/ingestion/validation/validate.py
from __future__ import annotations

from langchain_core.documents import Document
from hr_agent.core.settings import get_chunking_config

from hr_agent.ingest.validation.checks import (
    _preview,
    check_breadcrumb_coverage,
    check_chunk_length,
    check_orphaned_headers,
)

from hr_agent.ingest.validation.models import FlaggedChunk, ValidationReport

_cfg = get_chunking_config()


def validate_chunks(
    chunks: list[Document],
    min_chars: int = _cfg.length.min_chars,
    max_chars: int = _cfg.length.max_chars,
    max_examples_per_reason: int = 20,
) -> ValidationReport:
    """
    Run all three checks over `chunks` and return a ValidationReport.

    Does not raise or mutate `chunks` — purely diagnostic. Call right after
    chunking and again after any change to `txt_to_markdown()` to compare.
    """
    report = ValidationReport(total_chunks=len(chunks))
    examples_per_reason: dict[str, int] = {}

    def _record(index: int, reason: str, detail: str, chunk: Document) -> None:
        count = examples_per_reason.get(reason, 0)
        if count < max_examples_per_reason:
            report.examples.append(
                FlaggedChunk(
                    index=index,
                    reason=reason,
                    detail=detail,
                    preview=_preview(chunk.page_content),
                )
            )
            examples_per_reason[reason] = count + 1

    for i, chunk in enumerate(chunks):
        orphan_detail = check_orphaned_headers(chunk)
        if orphan_detail is not None:
            report.orphaned_header_count += 1
            _record(i, "orphaned_header", orphan_detail, chunk)

        length_result = check_chunk_length(chunk, min_chars, max_chars)
        if length_result is not None:
            reason, detail = length_result
            if reason == "too_short":
                report.too_short_count += 1
            else:
                report.too_long_count += 1
            _record(i, reason, detail, chunk)

        breadcrumb_detail = check_breadcrumb_coverage(chunk)
        if breadcrumb_detail is not None:
            report.missing_breadcrumb_count += 1
            _record(i, "missing_breadcrumb", breadcrumb_detail, chunk)

    return report