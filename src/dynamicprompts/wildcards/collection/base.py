from __future__ import annotations

from abc import ABC, abstractmethod
from pathlib import Path
from typing import Iterable

from dynamicprompts.wildcards.item import WildcardItem


class WildcardCollection(ABC):
    """
    A wildcard collection, i.e. a collection of strings.
    """

    @abstractmethod
    def path(self) -> Path:
        raise NotImplementedError("...")

    @abstractmethod
    def get_values(self) -> Iterable[str | WildcardItem]:
        """
        Get the contents of this collection.
        """
        raise NotImplementedError("...")
