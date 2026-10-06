GROUNDEDNESS_CHECK_PROMPT = """Check whether the ANSWER is fully supported by the CONTEXT. If it is, return True. If it is not, return False.

CONTEXT: {context}\n\nANSWER: {answer}\n\n
Return valid JSON only, e.g. {{"grounded": true}} or {{"grounded": false}}
"""