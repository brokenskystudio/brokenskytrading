from typing import Protocol


class AIAnalysisProvider(Protocol):
    def explain(self, metrics: dict) -> dict: ...
