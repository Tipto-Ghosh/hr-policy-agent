from __future__ import annotations
from dataclasses import dataclass, field


@dataclass
class FlaggedChunk:
    index: int
    reason: str
    detail: str
    preview: str


@dataclass
class ValidationReport:
    total_chunks: int
    orphaned_header_count: int = 0
    too_short_count: int = 0
    too_long_count: int = 0
    missing_breadcrumb_count: int = 0
    examples: list[FlaggedChunk] = field(default_factory=list)

    def summary(self) -> str:
        """One-line, greppable, CI-friendly status string."""
        return (
            f"total_chunks={self.total_chunks} "
            f"orphaned_headers={self.orphaned_header_count} "
            f"too_short={self.too_short_count} "
            f"too_long={self.too_long_count} "
            f"missing_breadcrumb={self.missing_breadcrumb_count}"
        )

    
    def print_examples(self, reason: str | None = None, limit: int = 10) -> None: 
        """
        Print up to `limit` flagged examples.

        If `reason` is None, prints examples across all reasons.
        If `reason` is set, filters to that reason. If no examples match,
        prints a short notice so the caller can tell "silent success" from
        "typo'd reason string".
        """
        shown = 0
        for ex in self.examples:
            if reason is not None and ex.reason != reason:
                continue
            print(f"[{ex.index}] {ex.reason}: {ex.detail}")
            print(f"    {ex.preview!r}")
            shown += 1
            if shown >= limit:
                break
        if shown == 0:
            print(f"No examples for reason={reason!r}.")