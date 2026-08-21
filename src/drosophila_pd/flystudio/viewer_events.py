from dataclasses import dataclass, field
from typing import Callable, List

@dataclass
class ViewerEvents:
    """Event bus for the viewer application."""
    listeners: List[Callable] = field(default_factory=list)

    def subscribe(self, callback: Callable) -> None:
        self.listeners.append(callback)

    def dispatch(self, event_name: str, payload: dict) -> None:
        for listener in self.listeners:
            listener(event_name, payload)
