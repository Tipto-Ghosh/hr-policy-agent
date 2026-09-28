# src/hr_agent/llm/records.py
from __future__ import annotations
from dataclasses import dataclass, field


@dataclass
class CallRecord:
    node_name: str
    kind: str # "llm" | "tool"
    model_or_tool_key: str
    input_tokens: int = 0
    output_tokens: int = 0
    latency_ms: float = 0.0
    cost_usd: float = 0.0

    def summary(self) -> str:
        """One-line status string, greppable and CI-friendly."""
        return (
            f"{self.node_name} [{self.kind}:{self.model_or_tool_key}] "
            f"in={self.input_tokens} out={self.output_tokens} "
            f"latency_ms={self.latency_ms:.1f} cost_usd={self.cost_usd:.5f}"
        )


@dataclass
class UsageSummary:
    call_count: int
    total_input_tokens: int
    total_output_tokens: int
    total_latency_ms: float
    total_cost_usd: float
    by_node: dict[str, dict] = field(default_factory=dict)

    def print_table(self) -> None:
        print(
            f"{'node':<32} {'kind':<6} {'model/tool':<14} "
            f"{'in_tok':>7} {'out_tok':>7} {'latency_ms':>11} {'cost_usd':>10}"
        )
        for node_name, row in self.by_node.items():
            print(
                f"{node_name:<32} {row['kind']:<6} "
                f"{row['model_or_tool_key']:<14} "
                f"{row['input_tokens']:>7} {row['output_tokens']:>7} "
                f"{row['latency_ms']:>11.1f} {row['cost_usd']:>10.5f}"
            )
        print(" - " * 60)
        print(
            f"TOTAL calls={self.call_count} "
            f"in_tok={self.total_input_tokens} "
            f"out_tok={self.total_output_tokens} "
            f"latency_ms={self.total_latency_ms:.1f} "
            f"cost_usd={self.total_cost_usd:.5f}"
        )