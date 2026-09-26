from __future__ import annotations
import re 
from langchain_core.documents import Document

from hr_agent.core.settings import get_chunking_config

_cfg = get_chunking_config()
DEFAULT_MIN_CHARS = _cfg.length.min_chars
DEFAULT_MAX_CHARS = _cfg.length.max_chars
ORPHAN_BODY_THRESHOLD_CHARS = _cfg.length.orphan_body_threshold_chars

# A line consisting only of a markdown heading, e.g. "## 4.2.1 Salary policy"
_HEADING_LINE_RE = re.compile(r"^\s{0,3}#{1,6}\s+.+$", re.MULTILINE)


def _preview(text: str, length: int = 100) -> str:
    stripped = text.strip().replace("\n", " ")
    return stripped[:length] + ("..." if len(stripped) > length else "")


def check_orphaned_headers(chunk: Document) -> str | None:
    """
    Returns a detail string if this chunk contains a heading line but is
    otherwise (near) empty of body content, else None.

    Only applies when a heading is actually present — a short chunk with no
    heading is a `too_short` case, not an orphaned-header case.
    """
    text = chunk.page_content
    if not _HEADING_LINE_RE.search(text):
        return None
    body_without_headings = _HEADING_LINE_RE.sub("", text).strip()
    if len(body_without_headings) < ORPHAN_BODY_THRESHOLD_CHARS:
        return (
            f"only {len(body_without_headings)} non-heading chars "
            f"(threshold {ORPHAN_BODY_THRESHOLD_CHARS})"
        )
    return None

def check_chunk_length(
    chunk: Document,
    min_chars: int = DEFAULT_MIN_CHARS,
    max_chars: int = DEFAULT_MAX_CHARS,
) -> tuple[str, str] | None:
    """
    Returns ("too_short" | "too_long", detail) if `chunk` falls outside the
    configured length bounds, else None.
    """
    length = len(chunk.page_content.strip())
    if length < min_chars:
        return "too_short", f"{length} chars (min {min_chars})"
    if length > max_chars:
        return "too_long", f"{length} chars (max {max_chars})"
    return None

def check_breadcrumb_coverage(chunk: Document) -> str | None:
    """
    Returns a detail string if this chunk has no breadcrumb metadata, else
    None. Looks for `breadcrumb` first (field set by enrich_chunks), then
    falls back to any `Header *` key from MarkdownHeaderTextSplitter.
    """
    metadata = chunk.metadata
    if metadata.get("breadcrumb"):
        return None
    has_any_header_key = any(
        key.lower().startswith("header") and value
        for key, value in metadata.items()
    )
    if has_any_header_key:
        return None
    return "no 'breadcrumb' and no 'Header *' metadata present"