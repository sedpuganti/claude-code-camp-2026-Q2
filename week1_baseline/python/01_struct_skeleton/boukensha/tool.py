from dataclasses import dataclass
from typing import Any, Callable


@dataclass
class Tool:
    """A callable capability registered for an agent context."""

    name: str
    description: str
    parameters: dict[str, Any]
    handler: Callable[..., str]

    def __str__(self):
        return (
            f"#<Tool name={self.name} description={str(self.description)[:41]} "
            f"params={list(self.parameters.keys())}>"
        )

    __repr__ = __str__
