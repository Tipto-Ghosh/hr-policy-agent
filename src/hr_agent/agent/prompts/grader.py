KB_EVIDENCE_GRADE_PROMPT = """You are an evidence grader.

Question:
{question}

Private Knowledge Base evidence:
{context}

Can this private Knowledge Base evidence answer the question?

Return 'good' if it can answer.
Return 'weak' if it cannot answer.

Return valid JSON only, e.g. {{"grade": "good"}}
"""

WEB_EVIDENCE_GRADE_PROMPT = """You are an evidence grader.

Question:
{question}

Web Search evidence:
{context}

Can this web evidence answer the question?

Return 'good' if it can answer.
Return 'weak' if it cannot answer.

Return valid JSON only, e.g. {{"grade": "good"}}
"""