from __future__ import annotations

import dataclasses
from pathlib import Path
from typing import Sequence

from dynamicprompts.wildcards.collection.base import WildcardCollection
from dynamicprompts.wildcards.item import WildcardItem


@dataclasses.dataclass(frozen=True)
class ListWildcardCollection(WildcardCollection):
    """
    A wildcard collection that's just a list of wildcards.

    The default implementation uses this to represent wildcards loaded from
    a structured pantry JSON/YAML file.
    """

    entries: Sequence[str | WildcardItem]

    # Implementation-specific hint for the source of the wildcards.
    source: tuple[Path, str | None] = None

    # The literal key path as written in the source file, e.g. ("a", "b", "c")
    # for a nested mapping or ("a/b/c",) for a flat key. This lets diagnostics
    # distinguish two declarations that resolve to the same wildcard name.
    declared_key_path: tuple[str, ...] | None = None

    def path(self) -> Path:
        if self.source is None:
            return None
        return self.source[0]

    def __hash__(self):
        return hash(("ListWildcardCollection", self.source or tuple(self.entries)))

    def get_values(self) -> Sequence[str | WildcardItem]:
        return self.entries
