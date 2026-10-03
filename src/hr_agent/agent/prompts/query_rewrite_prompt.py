QUERY_REWRITE_PROMPT = """Rewrite the question for better retrieval.

Rules:
- Preserve the original intent.
- Make it specific and search-friendly.
- Do not answer the question.
- Return only the rewritten question.

Original Question:
{question}
"""