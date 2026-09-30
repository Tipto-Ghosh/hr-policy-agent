HISTORY_SUMMARY_PROMPT = """Summarize the following conversation for later use
as context. Preserve: the user's topic, any decisions made, and any unresolved
questions. Do NOT invent details. Keep it under 120 words.

Conversation:
{transcript}

Summary:
"""