from dataclasses import dataclass, field
from typing import List

@dataclass
class SelectionPanel:
    """UI abstraction for scene graph selection."""
    selected_items: List[str] = field(default_factory=list)

    def select(self, item_id: str) -> None:
        if item_id not in self.selected_items:
            self.selected_items.append(item_id)

    def clear(self) -> None:
        self.selected_items.clear()
