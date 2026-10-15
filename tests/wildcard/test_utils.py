from dynamicprompts.wildcards.collection.structured import _parse_structured_file_list


def test_structured_parsing_emits_no_warnings(caplog):
    assert list(_parse_structured_file_list(["a", "b", "c"])) == ["a", "b", "c"]
    assert not caplog.records


def test_structured_parsing_keeps_numeric_items(caplog):
    """
    YAML/JSON parse bare numbers as int/float rather than str.

    They are valid wildcard values and must not be dropped as unsupported items.
    """
    assert list(_parse_structured_file_list([123, 4.5, 0])) == ["123", "4.5", "0"]
    assert not caplog.records


def test_structured_parsing_keeps_numbers_alongside_strings(caplog):
    assert list(_parse_structured_file_list(["a", 1, "b", 2.5])) == [
        "a",
        "1",
        "b",
        "2.5",
    ]
    assert not caplog.records


def test_structured_parsing_does_not_treat_bool_as_number(caplog):
    """
    ``bool`` subclasses ``int`` in Python; it must not be stringified to "True".

    Bools are still unsupported and are reported, matching pre-existing behaviour.
    """
    assert list(_parse_structured_file_list([True])) == []
    assert caplog.records
