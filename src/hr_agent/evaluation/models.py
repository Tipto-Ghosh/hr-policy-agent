from __future__ import annotations
from dataclasses import dataclass, field
from typing import Protocol

class RetrievedDoc(Protocol):
    """
    Structural shape the evaluator needs from a retrieved chunk.
    """
    metadata: dict

@dataclass
class GoldenExample:
    question: str
    expected_breadcrumb_contains: str
    
@dataclass
class EvalResult:
    question: str
    expected_breadcrumb_contains: str
    hit: bool
    retrieved_breadcrumbs: list[str] = field(default_factory = list)
    
    def summary(self)-> str:
        status = "HIT" if self.hit else "MISS"
        return f"[{status}] Question: {self.question}"


@dataclass
class EvalReport:
    k: int 
    results: list[EvalResult] = field(default_factory = list)
    
    @property
    def recall_at_k(self) -> float:
        if not self.results:
            return 0.0
        hits = sum(1 for result in self.results if result.hit)
        return hits / len(self.results)
    
    @property
    def hits(self) -> int:
        return sum(1 for result in self.results if result.hit)
    
    def summary(self) -> str:
        return (
            f"Recall@{self.k}: {self.recall_at_k:.2%} "
            f"({self.hits}/{len(self.results)} hits)"
        )
    
    def print_report(self):
        for result in self.results:
            print(result.summary())
            print(f"     expected_contains: {result.expected_breadcrumb_contains!r}")
            print(f"     retrieved_breadcrumbs: {result.retrieved_breadcrumbs}")
        print("-" * 40)
        print(self.summary())