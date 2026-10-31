from typing import Protocol


class AIProvider(Protocol):
    """Future prose-only adapter; factual metrics remain deterministic inputs."""
    def explain(self, findings: list[dict]) -> str: ...
