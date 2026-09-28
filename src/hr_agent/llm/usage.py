from __future__ import annotations

from hr_agent.llm.pricing import estimate_llm_cost, estimate_tool_cost
from hr_agent.llm.records import CallRecord, UsageSummary
from hr_agent.llm.token_usage import extract_token_usage


class UsageRecorder:
    def __init__(self) -> None:
        self._records: list[CallRecord] = []

    def record_llm_call(
        self,
        node_name: str,
        model_key: str,
        response,
        latency_ms: float,
    ) -> CallRecord:
        input_tokens, output_tokens = extract_token_usage(response)
        record = CallRecord(
            node_name=node_name,
            kind="llm",
            model_or_tool_key=model_key,
            input_tokens=input_tokens,
            output_tokens=output_tokens,
            latency_ms=latency_ms,
            cost_usd=estimate_llm_cost(model_key, input_tokens, output_tokens),
        )
        self._records.append(record)
        return record

    def record_tool_call(
        self,
        node_name: str,
        tool_key: str,
        latency_ms: float,
    ) -> CallRecord:
        record = CallRecord(
            node_name=node_name,
            kind="tool",
            model_or_tool_key=tool_key,
            latency_ms=latency_ms,
            cost_usd=estimate_tool_cost(tool_key),
        )
        self._records.append(record)
        return record

    def as_list(self) -> list[CallRecord]:
        return list(self._records)

    def __len__(self) -> int:
        return len(self._records)

    def summarize(self) -> UsageSummary:
        return summarize_usage(self._records)


def summarize_usage(records: list[CallRecord]) -> UsageSummary:
    """
    Aggregate a list of CallRecords into totals + a per-node breakdown.

    `by_node` is keyed by node_name; if a node is called more than once in
    one run (e.g. retries), its numbers are summed rather than overwritten.
    """
    by_node: dict[str, dict] = {}
    total_input = 0
    total_output = 0
    total_latency = 0.0
    total_cost = 0.0

    for record in records:
        total_input += record.input_tokens
        total_output += record.output_tokens
        total_latency += record.latency_ms
        total_cost += record.cost_usd

        if record.node_name not in by_node:
            by_node[record.node_name] = {
                "kind": record.kind,
                "model_or_tool_key": record.model_or_tool_key,
                "input_tokens": 0,
                "output_tokens": 0,
                "latency_ms": 0.0,
                "cost_usd": 0.0,
            }
        row = by_node[record.node_name]
        row["input_tokens"] += record.input_tokens
        row["output_tokens"] += record.output_tokens
        row["latency_ms"] += record.latency_ms
        row["cost_usd"] += record.cost_usd

    return UsageSummary(
        call_count=len(records),
        total_input_tokens=total_input,
        total_output_tokens=total_output,
        total_latency_ms=total_latency,
        total_cost_usd=total_cost,
        by_node=by_node,
    )