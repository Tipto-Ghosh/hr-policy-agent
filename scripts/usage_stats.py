from __future__ import annotations
from hr_agent.core.settings import get_settings
from hr_agent.llm import UsageRecorder, time_call

def main():
    from langchain_groq import ChatGroq # noqa: PLC0415
    settings = get_settings()
    groq_llm = ChatGroq(
        model = "openai/gpt-oss-20b", 
        temperature = 0,
        api_key = settings.groq_api_key
    )

    recorder = UsageRecorder()

    with time_call() as timer:
        response = groq_llm.invoke("What is the notice period for resignation?")

    print("raw usage_metadata:", getattr(response, "usage_metadata", None))
    print("raw response_metadata:", getattr(response, "response_metadata", None))

    record = recorder.record_llm_call(
        "manual_test_call", "groq_llm", response, timer.elapsed_ms
    )
    print(record)

    assert record.input_tokens > 0, (
        "extract_token_usage() returned 0 input tokens — check which shape "
        "your ChatGroq version actually returns and extend "
        "extract_token_usage() if it's neither usage_metadata nor "
        "response_metadata['token_usage']."
    )

    summary = recorder.summarize()
    summary.print_table()


if __name__ == "__main__":
    main()