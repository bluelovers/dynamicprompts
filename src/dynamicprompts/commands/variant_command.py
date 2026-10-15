from __future__ import annotations

import dataclasses
import logging
from itertools import combinations
from typing import Generator, Iterable

from dynamicprompts.commands.base import Command
from dynamicprompts.commands.literal_command import LiteralCommand
from dynamicprompts.enums import SamplingMethod
from dynamicprompts.utils import _fix_max_bound

logger = logging.getLogger(__name__)


@dataclasses.dataclass(frozen=True)
class VariantOption:
    value: Command
    weight: float = 1.0


@dataclasses.dataclass(frozen=True)
class VariantCommand(Command):
    variants: list[VariantOption]
    min_bound: int = 1
    max_bound: int | None = None
    separator: str = ","
    # Declared with `^`: pick randomly, but emit the chosen options in the
    # order they were declared rather than the order they were picked.
    preserve_order: bool = False
    # sampling_method: SamplingMethod | None = None

    def __post_init__(self):
        min_bound = self.min_bound
        if self.max_bound:
            min_bound, max_bound = sorted((self.min_bound, self.max_bound))
            object.__setattr__(self, "max_bound", max_bound)
        min_bound = max(0, min_bound)
        object.__setattr__(self, "min_bound", min_bound)

    def __len__(self) -> int:
        return len(self.variants)

    def __getitem__(self, index: int) -> VariantOption:
        return self.variants[index]

    def __iter__(self) -> Iterable[VariantOption]:
        return iter(self.variants)

    @property
    def weights(self) -> list[float]:
        return [p.weight for p in self.variants]

    @property
    def values(self) -> list[Command]:
        return [p.value for p in self.variants]

    def adjust_range(self) -> VariantCommand:
        max_options = len(self.variants)
        min_bound = min(self.min_bound, max_options)
        max_bound = _fix_max_bound(self.max_bound, max_options)
        return dataclasses.replace(self, min_bound=min_bound, max_bound=max_bound)

    @classmethod
    def from_literals_and_weights(
        cls,
        literals: list[str],
        weights: list[float] | None = None,
        min_bound: int = 1,
        max_bound: int = 1,
        separator: str = ",",
        sampling_method: SamplingMethod | None = None,
    ) -> VariantCommand:
        vals = [LiteralCommand(str(v)) for v in literals]
        if weights is None:
            weights = [1.0] * len(vals)
        assert len(vals) == len(weights), "Must have same number of weights as values"
        return VariantCommand(
            variants=[VariantOption(v, w) for v, w in zip(vals, weights)],
            min_bound=min_bound,
            max_bound=max_bound,
            separator=separator,
            sampling_method=sampling_method,
        )

    def get_value_combinations(
        self,
        k: int,
        values=None,
        *,
        preserve_order: bool = False,
    ) -> Generator[list[Command], None, None]:
        if values is None:
            values = self.values

        if preserve_order:
            # Declaration order: enumerate k-subsets only, never permutations.
            # `combinations` walks its input left to right, so every subset it
            # yields is already in the order the options were declared.
            if k <= 0:
                yield []
            else:
                yield from (list(c) for c in combinations(values, k))
            return

        if k <= 0:
            yield []
        else:
            for value in values:
                other_values = [v for v in values if v != value]
                for item in self.get_value_combinations(
                    k - 1,
                    values=other_values,
                    preserve_order=preserve_order,
                ):
                    yield [value] + item
