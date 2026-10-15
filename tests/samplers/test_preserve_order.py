from __future__ import annotations

import pytest
from dynamicprompts.generators.combinatorial import CombinatorialPromptGenerator
from dynamicprompts.generators.randomprompt import RandomPromptGenerator

ORDER = "abcde"


def _is_declaration_order(value: str) -> bool:
    indices = [ORDER.index(ch) for ch in value.split(",")]
    return indices == sorted(indices)


class TestPreserveOrderRandom:
    def test_every_result_is_in_declaration_order(self):
        generator = RandomPromptGenerator()

        results = [generator.generate("{~^3$$a|b|c|d|e}", 1)[0] for _ in range(50)]

        assert all(_is_declaration_order(r) for r in results), [
            r for r in results if not _is_declaration_order(r)
        ]

    def test_still_picks_a_variety_of_subsets(self):
        """preserve_order constrains output order, not which subsets get picked."""
        generator = RandomPromptGenerator()

        results = {generator.generate("{~^3$$a|b|c|d|e}", 1)[0] for _ in range(50)}

        # C(5,3) = 10 possible subsets; 50 draws must not collapse to one.
        assert len(results) > 1
        assert all(_is_declaration_order(r) for r in results)

    def test_without_caret_the_old_behaviour_remains(self):
        """Regression guard: omitting `^` must keep the original ordering."""
        generator = RandomPromptGenerator()

        results = [generator.generate("{~3$$a|b|c|d|e}", 1)[0] for _ in range(50)]

        assert any(not _is_declaration_order(r) for r in results)


class TestPreserveOrderCombinatorial:
    def test_caret_collapses_permutations_into_combinations(self):
        generator = CombinatorialPromptGenerator()

        without = generator.generate("{!2$$a|b|c|d}", 100)
        with_caret = generator.generate("{!^2$$a|b|c|d}", 100)

        # Default enumerates every ordering: P(4,2) = 12.
        assert len(without) == 12
        # With `^`: only declaration-ordered subsets, C(4,2) = 6.
        assert len(with_caret) == 6
        assert with_caret == ["a,b", "a,c", "a,d", "b,c", "b,d", "c,d"]

    def test_caret_combinations_are_all_ordered(self):
        generator = CombinatorialPromptGenerator()

        results = generator.generate("{!^3$$a|b|c|d|e}", 200)

        assert len(results) == 10  # C(5,3)
        assert all(_is_declaration_order(r) for r in results)

    @pytest.mark.parametrize("separator", [",", " and "])
    def test_respects_custom_separator(self, separator: str):
        generator = CombinatorialPromptGenerator()
        template = "{!^2$$ and $$a|b|c}" if separator == " and " else "{!^2$$a|b|c}"

        results = generator.generate(template, 100)

        expected = [
            f"a{separator}b",
            f"a{separator}c",
            f"b{separator}c",
        ]
        assert results == expected
