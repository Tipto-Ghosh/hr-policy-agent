from __future__ import annotations
import re 
from hr_agent.core.settings import get_chunking_config
_cfg = get_chunking_config()

_HEADER_STRIP_RE = re.compile(r"(?i)gesci\s*\n?\s*Founded by UN ICT Task Force")

_RE_SECTION = re.compile(_cfg.header_regexes.section)
_RE_SUBSECTION = re.compile(_cfg.header_regexes.subsection)
_RE_SUBSUBSECTION = re.compile(_cfg.header_regexes.subsubsection)
_RE_SUBSUBSUB = re.compile(_cfg.header_regexes.subsubsubsection)

def strip_running_headers(text: str) -> str:
    """Remove the repeated 'gesci / Founded by ...' running header."""
    return _HEADER_STRIP_RE.sub("", text).strip()

def txt_to_markdown(text: str) -> str:
    """
    Promote plain-text headers into markdown headers (#, ##, ###, ####) so
    MarkdownHeaderTextSplitter can build a hierarchy.

    Header promotion is driven by config/chunking.yaml's header_regexes plus
    structural heuristics (ALL CAPS, Title Case lines under 80/100/120 chars).
    """
    lines = text.split("\n")
    out: list[str] = []

    for line in lines:
        s = line.strip()
        if not s:
            out.append("")
            continue

        if _RE_SECTION.match(s) and len(s) < 80:
            out.append(f"\n# {s}\n")
        elif _RE_SUBSECTION.match(s) and len(s) < 100:
            out.append(f"\n## {s}\n")
        elif _RE_SUBSUBSECTION.match(s) and len(s) < 120:
            out.append(f"\n### {s}\n")
        elif _RE_SUBSUBSUB.match(s) and len(s) < 120:
            out.append(f"\n#### {s}\n")
        elif s.isupper() and len(s) < 80 and len(s.split()) <= 10:
            out.append(f"\n# {s}\n")
        elif (
            s.istitle()
            and len(s) < 80
            and not s.endswith(".")
            and len(s.split()) <= 8
        ):
            out.append(f"\n## {s}\n")
        else:
            out.append(s)

    return "\n".join(out)