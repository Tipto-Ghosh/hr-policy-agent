MEMORY_EXTRACT_PROMPT = """You extract durable USER PREFERENCES from one
conversation turn. Do NOT extract facts, case details, names, or any content
about a specific HR situation.

Allowed keys (only these, no others):
- language        (e.g. "en", "bn")
- verbosity       ("concise" or "detailed")
- format          ("bullets", "prose", or "table")
- recurring_topic (a single lowercase topic word like "leave", "travel", "discipline")

If there are no durable preferences in this turn, return [].

User question:
{question}

Assistant answer:
{answer}

Return valid JSON only: a list of objects, e.g.
[{{"key": "verbosity", "value": "concise"}}]
"""