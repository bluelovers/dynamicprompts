from __future__ import annotations

import dataclasses
from typing import Optional

from dynamicprompts.enums import SamplingMethod


@dataclasses.dataclass(frozen=True, kw_only=True)
class Command:
    """Base class for commands."""

    sampling_method: Optional[SamplingMethod] = None
    immediate: Optional[bool] = None
