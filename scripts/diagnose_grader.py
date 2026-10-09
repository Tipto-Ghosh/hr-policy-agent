from hr_agent.agent.runner import default_deps
from hr_agent.agent.nodes.grade_kb import make_grade_kb_node
from hr_agent.agent.prompts.grader import KB_EVIDENCE_GRADE_PROMPT
from hr_agent.retrieval import get_retriever

QUESTION = "Does GESCI provide equal hiring opportunities to all employees?"

retriever = get_retriever()
docs = retriever.invoke(QUESTION)

context = "\n\n".join(
    f"Source: {d.metadata.get('source')}\n{d.page_content}"
    for d in docs
)
prompt = KB_EVIDENCE_GRADE_PROMPT.format(question=QUESTION, context=context)

print("=" * 80)
print("PROMPT SENT TO GRADER")
print("=" * 80)
print(prompt)

deps = default_deps()
grader = deps.llms.kb_grader

print("\n" + "=" * 80)
print("GRADER RESPONSE")
print("=" * 80)
result = grader.invoke(prompt)
print(result)