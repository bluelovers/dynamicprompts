"""
Shared, reusable diagnostics helpers.

This module centralises how the library reports structural problems (for example
two different YAML key shapes that resolve to the same wildcard name) so that the
same enrichment - source file, key path and calling code location - can be reused
and improved in one place rather than being re-implemented per call site.

The main entry point is :func:`assign_checked`, which behaves like a plain
``mapping[key] = value`` but warns when the assignment silently overwrites an
existing entry.

:copyright: (c) the dynamicprompts contributors
:license: MIT
"""

from __future__ import annotations

import dataclasses
import enum
import inspect
import logging
from pathlib import Path
from typing import Any, Callable, MutableMapping, TypeVar

logger = logging.getLogger(__name__)

K = TypeVar("K")
V = TypeVar("V")


class DiagnosticKind(str, enum.Enum):
    """
    Categories of structural diagnostics emitted by the library.

    Using an enum (rather than free-form strings) lets call sites and tests
    filter on a stable identifier while the rendered message can still evolve.
    """

    NAME_COLLISION = "name-collision"


@dataclasses.dataclass(frozen=True)
class SourceRef:
    """
    A reference to where a value came from.

    Both fields are optional because not every value can be traced back to a
    file or a key; :meth:`describe` degrades gracefully when they are missing.
    """

    file: Path | None = None
    key: str | None = None
    declared: tuple[str, ...] | None = None

    def describe(self) -> str:
        """
        Render a short, human-readable description of this source.
        """
        if self.file is None and self.key is None and not self.declared:
            return "an unknown source"

        parts: list[str] = []
        if self.file is not None:
            parts.append(f"file {self.file}")
        if self.declared:
            # Show the literal YAML/JSON key path as written, so that a nested
            # `a: b: c:` can be told apart from a flat `a/b/c:` even though both
            # resolve to the same wildcard name.
            parts.append(f"key {' / '.join(repr(p) for p in self.declared)}")
        elif self.key:
            parts.append(f"key {self.key!r}")
        return ", ".join(parts)

    @classmethod
    def from_value(cls, value: Any) -> SourceRef:
        """
        Best-effort extraction of a :class:`SourceRef` from an arbitrary value.

        Understands the conventions already used in this package:

        * a ``source`` attribute holding a ``(file_path, key_or_None)`` tuple, as
          set by :class:`~dynamicprompts.wildcards.collection.list.ListWildcardCollection`
        * a ``path()`` method returning a :class:`~pathlib.Path`, as implemented
          by every :class:`~dynamicprompts.wildcards.collection.base.WildcardCollection`
        """
        source = getattr(value, "source", None)
        if isinstance(source, tuple) and source:
            file = source[0] if source[0] is not None else None
            key = source[1] if len(source) > 1 else None
            if file is not None or key:
                return cls(
                    file=Path(file) if file is not None else None,
                    key=key,
                    declared=getattr(value, "declared_key_path", None),
                )

        path = getattr(value, "path", None)
        if callable(path):
            resolved = path()
            if resolved is not None:
                return cls(file=Path(resolved))

        return cls()


@dataclasses.dataclass(frozen=True)
class CallerSite:
    """
    The source location that triggered a diagnostic.
    """

    file: Path
    line: int
    function: str

    def describe(self) -> str:
        return f"{self.file}:{self.line} in {self.function}()"

    @classmethod
    def capture(cls, *, skip: int = 0) -> CallerSite:
        """
        Capture the caller's location.

        :param skip: number of extra stack frames to skip past this function and
            its immediate caller.
        """
        frame = inspect.currentframe()
        try:
            for _ in range(skip + 1):
                frame = frame.f_back if frame is not None else None
            if frame is None:  # pragma: no cover - only on unsupported interpreters
                return cls(file=Path("<unknown>"), line=0, function="<unknown>")
            return cls(
                file=Path(frame.f_code.co_filename),
                line=frame.f_lineno,
                function=frame.f_code.co_name,
            )
        finally:
            # Avoid reference cycles (https://docs.python.org/3/library/inspect.html)
            del frame


@dataclasses.dataclass(frozen=True)
class Diagnostic:
    """
    A single, structured diagnostic report.

    Keeping the pieces as fields (rather than only a pre-rendered string) lets
    callers filter by :attr:`kind` and lets the rendering change independently.
    """

    kind: DiagnosticKind
    message: str
    source: SourceRef | None = None
    previous_source: SourceRef | None = None
    site: CallerSite | None = None

    def render(self) -> str:
        """
        Render the full, human-readable warning text.
        """
        chunks = [self.message]

        if self.source is not None and self.source != self.previous_source:
            chunks.append(f"new value from {self.source.describe()}")
        if self.previous_source is not None:
            chunks.append(f"overwrites {self.previous_source.describe()}")
        if self.site is not None:
            chunks.append(f"first registered at {self.site.describe()}")

        return "; ".join(chunks)

    def emit(
        self,
        log: logging.Logger | None = None,
        *,
        level: int = logging.WARNING,
    ) -> None:
        """
        Emit this diagnostic through ``log`` (defaults to this module's logger).
        """
        (log or logger).log(level, self.render())


def name_collision(
    name: K,
    *,
    new_value: Any,
    old_value: Any,
    site: CallerSite | None = None,
) -> Diagnostic:
    """
    Build a :class:`Diagnostic` describing ``name`` being overwritten.
    """
    return Diagnostic(
        kind=DiagnosticKind.NAME_COLLISION,
        message=f"Duplicate wildcard name {str(name)!r}",
        source=SourceRef.from_value(new_value),
        previous_source=SourceRef.from_value(old_value),
        site=site,
    )


def assign_checked(
    mapping: MutableMapping[K, V],
    key: K,
    value: V,
    *,
    on_collision: Callable[[K, V, V], Diagnostic] | None = None,
    log: logging.Logger | None = None,
    site: CallerSite | None = None,
) -> V:
    """
    Assign ``mapping[key] = value``, warning if it overwrites an existing entry.

    This is a drop-in replacement for a plain mapping assignment that adds a
    diagnostic when two independent definitions resolve to the same key. It is
    deliberately generic (any mapping, any value type) so it can be reused
    wherever a silent overwrite is possible.

    :param mapping: mapping to assign into; mutated in place.
    :param key: key to assign under.
    :param value: value to assign.
    :param on_collision: optional factory building the :class:`Diagnostic`;
        defaults to :func:`name_collision`.
    :param log: logger to emit through; defaults to this module's logger.
    :param site: caller site to report; captured automatically when omitted.
    :return: the assigned value.
    """
    if key not in mapping:
        mapping[key] = value
        return value

    if site is None:
        site = CallerSite.capture(skip=1)

    factory = on_collision or name_collision
    diagnostic = factory(key, new_value=value, old_value=mapping[key], site=site)
    diagnostic.emit(log)
    mapping[key] = value
    return value


__all__ = [
    "CallerSite",
    "Diagnostic",
    "DiagnosticKind",
    "SourceRef",
    "assign_checked",
    "name_collision",
]
