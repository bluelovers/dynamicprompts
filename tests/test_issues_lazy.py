from itertools import islice

from dynamicprompts.enums import SamplingMethod
from dynamicprompts.parser.parse import parse
from dynamicprompts.sampling_context import SamplingContext
from dynamicprompts.wildcards import WildcardManager

def test_issues_bug_zipper(wildcard_manager: WildcardManager):
    _lazy_test(wildcard_manager, "{1-$$__lazy-wildcards/subject/costume-elem-accessories/zipper/style__}")

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
