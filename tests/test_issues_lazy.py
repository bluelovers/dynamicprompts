from itertools import islice

from dynamicprompts.enums import SamplingMethod
from dynamicprompts.parser.parse import parse
from dynamicprompts.sampling_context import SamplingContext
from dynamicprompts.wildcards import WildcardManager


def test_fn_var_should_work_a01(wildcard_manager: WildcardManager):
    _lazy_test(wildcard_manager, "{1-$$__lazy-wildcards/subject/costume-elem-accessories/zipper/style_a01__}")

def test_fn_var_should_work_but_dont_use_a02(wildcard_manager: WildcardManager):
    _lazy_test(wildcard_manager, "{1-$$__lazy-wildcards/subject/costume-elem-accessories/zipper/style_a02__}")

def test_fn_var_should_work_but_dont_use_a03(wildcard_manager: WildcardManager):
    _lazy_test(wildcard_manager, "{1-$$__lazy-wildcards/subject/costume-elem-accessories/zipper/style_a03__}")

def test_fn_var_should_work_but_dont_use_b01(wildcard_manager: WildcardManager):
    _lazy_test(wildcard_manager, "{1-$$__lazy-wildcards/subject/costume-elem-accessories/zipper/style_b01__}")

def _lazy_test(wildcard_manager: WildcardManager, prompts: str):
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
        seen.add(prompt)
    print(seen)

    print("Used wildcards:", scon.wildcard_manager.used_collection_dict().keys())
