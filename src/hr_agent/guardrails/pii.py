from __future__ import annotations
import re
from dataclasses import dataclass
from functools import lru_cache
from hr_agent.core.settings import get_settings, get_guardrails_config


@dataclass(frozen = True)
class PiiSpan:
    start: int
    end: int
    label: str
    score: float = 1.0
    
def find_regex_spans(text: str) -> list[PiiSpan]:
    """
    Find spans of PII in the text using regex patterns.
    """
    config = get_guardrails_config()
    spans = []
    for label, pattern in config.pii.regex_patterns.items():
        for match in re.finditer(pattern, text):
            spans.append(
                PiiSpan(
                  start = match.start(), 
                  end = match.end(), 
                  label = label
                )
            )
    return spans

def _apply_spans(text: str, spans: list[PiiSpan]) -> str:
    """
    Replace each span's text with '<LABEL>', working right to left so earlier
    offsets stay valid as the string is modified.
    """
    masked = text
    for span in sorted(spans, key=lambda s: s.start, reverse=True):
        masked = masked[:span.start] + f"<{span.label}>" + masked[span.end:]
    
    return masked

def mask_pii_regex(text: str) -> str:
    """
    Regex-only masking of PII in the text. 
    """
    spans = find_regex_spans(text)
    return _apply_spans(text, spans)


@lru_cache
def get_analyzer():
    """
    Lazy singleton AnalyzerEngine, built once per process.
    """
    from presidio_analyzer import AnalyzerEngine
    from presidio_analyzer.nlp_engine import NlpEngineProvider

    settings = get_settings()
    provider = NlpEngineProvider(
        nlp_configuration = {
            "nlp_engine_name": "spacy",
            "models": [
                {"lang_code": "en", "model_name": settings.spacy_model_name}
            ]
        }
    )
    nlp_engine = provider.create_engine()
    return AnalyzerEngine(
        nlp_engine = nlp_engine,
        supported_languages = ["en"]
    )
    
def find_presidio_spans(text: str) -> list[PiiSpan]:
    """Run Presidio against `text`, return spans for configured entities
    above the configured score threshold."""
    config = get_guardrails_config().pii
    if not config.presidio_entities:
        return []
 
    analyzer = get_analyzer()
    results = analyzer.analyze(
        text=text,
        entities=config.presidio_entities,
        language=config.presidio_language,
        score_threshold=config.presidio_score_threshold,
    )
    return [
        PiiSpan(r.start, r.end, r.entity_type, r.score) for r in results
    ]
    

def mask_pii_presidio(text: str) -> str:
    """
    Presidio-based masking of PII in the text. 
    """
    spans = find_presidio_spans(text)
    return _apply_spans(text, spans)


def merge_spans(
    regex_spans: list[PiiSpan], presidio_spans: list[PiiSpan]
) -> list[PiiSpan]:
    """
    Merge the two span lists, resolving overlaps with regex taking priority.
 
    Algorithm: sort all spans by start index; walk through, keeping a span
    unless it overlaps one already kept. Regex spans are inserted first so
    that when a presidio span overlaps a regex span, the regex span (already
    kept) blocks it.
    """
    combined = sorted(regex_spans, key=lambda s: s.start) + sorted(
        presidio_spans, key=lambda s: s.start
    )
    # Stable merge: process regex spans fully first (they always win),
    # then add non-overlapping presidio spans.
    kept: list[PiiSpan] = list(sorted(regex_spans, key=lambda s: s.start))
 
    def overlaps(a: PiiSpan, b: PiiSpan) -> bool:
        return a.start < b.end and b.start < a.end
 
    for p_span in sorted(presidio_spans, key=lambda s: s.start):
        if not any(overlaps(p_span, k) for k in kept):
            kept.append(p_span)
 
    return sorted(kept, key=lambda s: s.start)


def mask_pii(text: str) -> str:
    """
    Public entry point used by the agent's input guard.
    """
    if not text:
        return text
    
    regex_spans = find_regex_spans(text)
    presidio_spans = find_presidio_spans(text)
    merged_spans = merge_spans(regex_spans, presidio_spans)
    return _apply_spans(text, merged_spans)