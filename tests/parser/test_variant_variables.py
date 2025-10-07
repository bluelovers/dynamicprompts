from __future__ import annotations

from typing import cast

from dynamicprompts.commands import LiteralCommand, SequenceCommand, VariantCommand
from dynamicprompts.commands.variable_commands import (
    VariableAccessCommand,
    VariableAssignmentCommand,
)
from dynamicprompts.parser.parse import parse


def test_variables_inside_variants():
    cmd = parse("{a ${v}|b ${v}|c ${v}}")
    assert isinstance(cmd, VariantCommand)
    assert len(cmd) == 3

    # Check each option is a sequence: literal + variable access
    for i, expected_literal in enumerate(["a ", "b ", "c "]):
        seq = cast(SequenceCommand, cmd.values[i])
        assert isinstance(seq, SequenceCommand)
        assert len(seq) == 2
        lit, var = seq.tokens
        assert isinstance(lit, LiteralCommand)
        assert lit.literal == expected_literal
        assert isinstance(var, VariableAccessCommand)
        assert var.name == "v"


def test_variable_assignment_then_variant_with_access():
    cmd = parse("${v=123}\n{a ${v}|b ${v}|c ${v}}")
    # Entire prompt is a sequence: assignment, newline, variant
    assert isinstance(cmd, SequenceCommand)
    assert len(cmd) == 3

    ass, newline, variant = cmd.tokens
    assert isinstance(ass, VariableAssignmentCommand)
    assert ass.name == "v"
    assert isinstance(ass.value, LiteralCommand)
    assert ass.value.literal == "123"

    assert isinstance(newline, LiteralCommand)
    assert newline.literal == "\n"

    assert isinstance(variant, VariantCommand)
    assert len(variant) == 3

    for i, expected_literal in enumerate(["a ", "b ", "c "]):
        seq = cast(SequenceCommand, variant.values[i])
        assert isinstance(seq, SequenceCommand)
        assert len(seq) == 2
        lit, var = seq.tokens
        assert isinstance(lit, LiteralCommand)
        assert lit.literal == expected_literal
        assert isinstance(var, VariableAccessCommand)
        assert var.name == "v"
