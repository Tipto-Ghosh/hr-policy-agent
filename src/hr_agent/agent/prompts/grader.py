KB_EVIDENCE_GRADE_PROMPT = """You are an evidence grader for an HR policy assistant.

Decide whether the provided evidence contains information that answers the
user's question.

Question:
{question}

Evidence:
{context}

How to decide:
- Grade 'good' if the evidence answers the question OR contains a policy
  statement on the same subject, even if the wording does not exactly match.
- Grade 'good' if the evidence states a rule, requirement, expectation, or
  permission that a reasonable reader would accept as the answer.
- Grade 'weak' ONLY if the evidence is about a different topic, or is silent
  on the subject of the question.

Examples of 'good':
- Q: "Should an employee have a Skype account?" / Evidence: "Staff should
  have a GESCI Skype account for business purposes." → good (direct policy
  statement that answers the question).
- Q: "What is the notice period for resignation?" / Evidence: "A staff
  member resigning must give GESCI four weeks written notice." → good.
- Q: "Does GESCI offer equal opportunities?" / Evidence: "GESCI provides
  equal employment opportunities to all qualified staff." → good.

Examples of 'weak':
- Q: "What is the notice period for resignation?" / Evidence discusses only
  annual leave. → weak.
- Q: "How does bereavement leave work?" / Evidence has nothing on
  bereavement. → weak.

Return JSON only: {{"grade": "good"}} or {{"grade": "weak"}}
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