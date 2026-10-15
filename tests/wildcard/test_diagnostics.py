import logging
from pathlib import Path

from dynamicprompts.diagnostics import (
    DiagnosticKind,
    SourceRef,
    assign_checked,
    name_collision,
)
from dynamicprompts.wildcards.collection.list import ListWildcardCollection
from dynamicprompts.wildcards.tree.build import build_tree_from_path


def test_no_collision_is_silent(caplog):
    mapping = {}
    with caplog.at_level(logging.WARNING):
        assign_checked(mapping, "a", "1")
        assign_checked(mapping, "b", "2")
    assert mapping == {"a": "1", "b": "2"}
    assert not caplog.records


def test_collision_overwrites_and_returns_new_value(caplog):
    mapping = {}
    assign_checked(mapping, "a", "old")
    with caplog.at_level(logging.WARNING):
        result = assign_checked(mapping, "a", "new")

    # Still a plain dict assignment at heart: last write wins.
    assert result == "new"
    assert mapping == {"a": "new"}
    assert len(caplog.records) == 1


def test_collision_message_includes_name_and_both_sources(caplog):
    old = ListWildcardCollection(entries=["1"], source=(Path("old.yaml"), "a"))
    new = ListWildcardCollection(entries=["2"], source=(Path("new.yaml"), "a"))

    mapping = {"a": old}
    with caplog.at_level(logging.WARNING):
        assign_checked(mapping, "a", new)

    message = caplog.records[0].getMessage()
    assert "'a'" in message
    assert "old.yaml" in message
    assert "new.yaml" in message


def test_collision_reports_caller_site(caplog):
    mapping = {"a": "old"}

    with caplog.at_level(logging.WARNING):
        # This call site is what the diagnostic should report.
        assign_checked(mapping, "a", "new")

    message = caplog.records[0].getMessage()
    assert "test_diagnostics.py" in message
    # We report the caller's function, not the diagnostics helper itself.
    assert "test_collision_reports_caller_site" in message
    assert "assign_checked" not in message


def test_distinguishes_nested_from_flat_yaml_keys(tmp_path):
    """
    A nested `a: b: c:` and a flat `a/b/c:` resolve to the same wildcard name.
    The warning must show the literal declared key path for both sides so the
    user can tell which one overwrote which.
    """
    (tmp_path / "a.yaml").write_text(
        'a:\n  b:\n    c:\n      - "123"\n\n"a/b/c":\n  - "456"\n',
        encoding="utf-8",
    )

    with caplog_at_warning() as capture:
        build_tree_from_path(tmp_path)

    collisions = [
        r for r in capture.records if "Duplicate wildcard name" in r.getMessage()
    ]
    assert len(collisions) == 1

    message = collisions[0].getMessage()
    # Flat declaration
    assert "'a/b/c'" in message
    # Nested declaration, rendered as separate segments
    assert "'a' / 'b' / 'c'" in message


class caplog_at_warning:
    """Minimal context manager capturing WARNING+ records from dynamicprompts."""

    def __init__(self):
        self.records = []

    def __enter__(self):
        self._logger = logging.getLogger("dynamicprompts")
        self._level = self._logger.level
        self._handler = _Collector(self.records)
        self._logger.addHandler(self._handler)
        self._logger.setLevel(logging.WARNING)
        return self

    def __exit__(self, *exc):
        self._logger.removeHandler(self._handler)
        self._logger.setLevel(self._level)
        return False


class _Collector(logging.Handler):
    def __init__(self, sink):
        super().__init__()
        self._sink = sink

    def emit(self, record):
        self._sink.append(record)


def test_source_ref_falls_back_to_path_method():
    class HasPath:
        def path(self):
            return Path("only.txt")

    ref = SourceRef.from_value(HasPath())
    assert ref.file == Path("only.txt")
    assert ref.key is None


def test_source_ref_unknown():
    ref = SourceRef.from_value(object())
    assert ref.describe() == "an unknown source"


def test_name_collision_kind():
    d = name_collision("x", new_value="n", old_value="o")
    assert d.kind == DiagnosticKind.NAME_COLLISION
