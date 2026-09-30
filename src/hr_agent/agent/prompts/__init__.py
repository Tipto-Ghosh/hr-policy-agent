from hr_agent.agent.prompts.direct_answer import DIRECT_ANSWER_PROMPT
from hr_agent.agent.prompts.generation import (
    KB_GENERATION_PROMPT,
    WEB_GENERATION_PROMPT,
)
from hr_agent.agent.prompts.grader import (
    KB_EVIDENCE_GRADE_PROMPT,
    WEB_EVIDENCE_GRADE_PROMPT,
)
from hr_agent.agent.prompts.history_summary import HISTORY_SUMMARY_PROMPT
from hr_agent.agent.prompts.memory_extract import MEMORY_EXTRACT_PROMPT
from hr_agent.agent.prompts.router import ROUTER_PROMPT
from hr_agent.agent.prompts.scope import SCOPE_PROMPT

__all__ = [
    "SCOPE_PROMPT",
    "ROUTER_PROMPT",
    "KB_EVIDENCE_GRADE_PROMPT",
    "WEB_EVIDENCE_GRADE_PROMPT",
    "KB_GENERATION_PROMPT",
    "WEB_GENERATION_PROMPT",
    "DIRECT_ANSWER_PROMPT",
    "MEMORY_EXTRACT_PROMPT",
    "HISTORY_SUMMARY_PROMPT",
]