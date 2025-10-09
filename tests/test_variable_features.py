from itertools import islice

from dynamicprompts.enums import SamplingMethod
from dynamicprompts.parser.parse import parse
from dynamicprompts.sampling_context import SamplingContext
from dynamicprompts.wildcards import WildcardManager


def test_discussion_61(wildcard_manager: WildcardManager):
    _lazy_test(wildcard_manager, "${animal={fox|manatee}} __publicprompts/plush-toy__",
               {"cute kawaii squishy fox", "cute kawaii squishy manatee"}, "cute kawaii squishy")


def test_discussion_61_shorthand(wildcard_manager: WildcardManager):
    cmd = parse("__publicprompts/plush-toy(animal=fox)__")
    scon = SamplingContext(
        default_sampling_method=SamplingMethod.RANDOM,
        wildcard_manager=wildcard_manager,
    )
    prompt = str(next(scon.sample_prompts(cmd))).strip().lower()
    assert prompt.startswith("cute kawaii squishy fox")


def test_discussion_61_shorthand_immediate(wildcard_manager: WildcardManager):
    cmd = parse("__publicprompts/plush-toy(animal=!fox)__")
    scon = SamplingContext(
        default_sampling_method=SamplingMethod.RANDOM,
        wildcard_manager=wildcard_manager,
    )
    prompt = str(next(scon.sample_prompts(cmd))).strip().lower()
    assert prompt.startswith("cute kawaii squishy fox")


def test_variant_range_with_variable_assignment(wildcard_manager: WildcardManager):
    # Parse template with variable assignment, newline, and ranged variant
    cmd = parse("${v=123}\n{2-$$a ${v}|b ${v}|c ${v}}")
    # Use COMBINATORIAL to ensure coverage of all combinations of 2-3 picks
    scon = SamplingContext(
        default_sampling_method=SamplingMethod.COMBINATORIAL,
        wildcard_manager=wildcard_manager,
    )
    gen = scon.sample_prompts(cmd)

    seen = set()
    expected = {"a 123", "b 123", "c 123"}

    # Collect prompts (combinatorial should be finite for this command)
    for prompt in gen:
        text = str(prompt)
        # print(f"prompt: {prompt}")
        # Split into lines; the second line contains the variant output
        lines = text.split("\n")
        if len(lines) >= 2:
            variant_line = lines[1].strip()
            # print(f"variant_line: {variant_line}")
            # Default separator is "," if not specified explicitly
            parts = [p.strip() for p in variant_line.split(",") if p.strip()]
            for part in parts:
                # print(f"part: {part}")
                if part in expected:
                    seen.add(part)
        # Stop early if all expected items have been seen
        if seen == expected:
            break

    assert seen == expected


def test_variant_fn_001(wildcard_manager: WildcardManager):
    _lazy_test(wildcard_manager, "__publicprompts/plush-toy(animal={fox|manatee})__",
               {"cute kawaii squishy fox", "cute kawaii squishy manatee"}, "cute kawaii squishy")


def test_variant_fn_001_immediate(wildcard_manager: WildcardManager):
    _lazy_test(wildcard_manager, "__publicprompts/plush-toy(animal=!{fox|manatee})__",
               {"cute kawaii squishy fox", "cute kawaii squishy manatee"}, "cute kawaii squishy")


def test_variant_fn_002(wildcard_manager: WildcardManager):
    _lazy_test(wildcard_manager, "__publicprompts/plush-toy(animal=fox)__",
               {"cute kawaii squishy fox"}, "cute kawaii squishy")


def test_variant_fn_002_immediate(wildcard_manager: WildcardManager):
    _lazy_test(wildcard_manager, "__publicprompts/plush-toy(animal=!fox)__",
               {"cute kawaii squishy fox"}, "cute kawaii squishy")


def test_variant_fn_003_immediate(wildcard_manager: WildcardManager):
    _lazy_test2(wildcard_manager, "__variant-fn/fn/test(v=!{fox|manatee})__",
               {"kawaii fox cute fox", "kawaii manatee cute manatee"}, "kawaii")


def test_variant_fn_004_immediate(wildcard_manager: WildcardManager):
    _lazy_test(wildcard_manager, "__variant-fn/prompts1__",
                {"kawaii fox cute fox", "kawaii manatee cute manatee"}, "kawaii")


def test_variant_fn_005_immediate(wildcard_manager: WildcardManager):
    _lazy_test(wildcard_manager, "__variant-fn/prompts2__",
                {"kawaii fox cute fox", "kawaii manatee cute manatee"}, "kawaii")


# def test_variant_fn_006_immediate(wildcard_manager: WildcardManager):
#     _lazy_test(wildcard_manager, "__variant-fn/prompts3__",
#                 {"kawaii fox cute fox", "kawaii manatee cute manatee"}, "kawaii")


def _lazy_test(wildcard_manager: WildcardManager, prompts: str, expected: set[str], startswith: str):
    cmd = parse(prompts)
    scon = SamplingContext(
        default_sampling_method=SamplingMethod.RANDOM,
        wildcard_manager=wildcard_manager,
    )

    gen = scon.sample_prompts(cmd)
    seen = set()
    for prompt in islice(gen, 10):
        prompt = str(prompt).strip().lower()
        # print(f"prompt: {prompt}")
        assert prompt.startswith(startswith)
        for ex in expected:
            if ex in prompt:
                seen.add(ex)
        if expected == seen:
            break
    assert seen == expected

    print("Used wildcards:", scon.wildcard_manager.used_collection_dict().keys())


def _lazy_test2(wildcard_manager: WildcardManager, prompts: str, expected: set[str], startswith: str):
    cmd = parse(prompts)
    scon = SamplingContext(
        default_sampling_method=SamplingMethod.RANDOM,
        wildcard_manager=wildcard_manager,
    )

    my_len = len(expected)

    gen = scon.sample_prompts(cmd)
    seen = set()
    for prompt in islice(gen, 10):
        prompt = str(prompt).strip().lower()
        # print(f"prompt: {prompt}")
        assert prompt.startswith(startswith)
        seen.add(prompt)
        if expected == seen or len(seen) >= my_len:
            break
    assert seen == expected

    print("Used wildcards:", scon.wildcard_manager.used_collection_dict().keys())
