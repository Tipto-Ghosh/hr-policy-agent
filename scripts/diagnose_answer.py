from hr_agent.retrieval import get_retriever
from hr_agent.agent.runner import ask_agent

Q = "should employee have a Skype Account?"

# --- Stage 1: raw retrieval ---
retriever = get_retriever()
docs = retriever.invoke(Q)
print(f"=== retrieval: {len(docs)} docs ===")
for i, d in enumerate(docs, 1):
    print(f"{i}. {d.metadata.get('breadcrumb', '(no breadcrumb)')}")
    print(f"   preview: {d.page_content.strip()}...")

# --- Stage 2: full graph run ---
r = ask_agent(question=Q, user_id="tipto", chat_id="diag-1", verbose=False)
print("\n=== graph run ===")
print("source_used :", r.get("source_used"))
print("grade       :", r.get("retrieved_docs_evidence_grade"))
print("current_query:", r.get("current_query"))
print("answer      :", r.get("answer", "")[:200])