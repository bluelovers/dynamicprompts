from __future__ import annotations
from itertools import chain
import logging

from dynamicprompts.wildcardmanager import WildcardManager
from dynamicprompts import constants
from . import PromptGenerator, re_combinations, re_wildcard

logger = logging.getLogger(__name__)


class BatchedCombinatorialPromptGenerator(PromptGenerator):
    def __init__(self, generator: PromptGenerator, batches=1):
        self._generator = generator
        self._batches = batches

    def generate(self, max_prompts=constants.MAX_IMAGES) -> list[str]:
        images = []

        for _ in range(self._batches):
            images.extend(self._generator.generate(max_prompts))
        return images