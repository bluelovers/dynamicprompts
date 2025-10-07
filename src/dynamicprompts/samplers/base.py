from __future__ import annotations

import logging

from dynamicprompts.commands import (
    Command,
    LiteralCommand,
    SequenceCommand,
    VariantCommand,
    WildcardCommand,
    WrapCommand,
)
from dynamicprompts.commands.variable_commands import (
    VariableAccessCommand,
    VariableAssignmentCommand,
)
from dynamicprompts.samplers.utils import wildcard_to_variant
from dynamicprompts.sampling_context import SamplingContext
from dynamicprompts.sampling_result import SamplingResult
from dynamicprompts.types import ResultGen
from dynamicprompts.utils import rotate_and_join

logger = logging.getLogger(__name__)


class Sampler:
    def generator_from_command(
        self,
        command: Command,
        context: SamplingContext,
    ) -> ResultGen:
        # This is purposely not a dict lookup/getattr magic thing, to make
        # it easier for code completion etc. to see what's going on.
        if isinstance(command, LiteralCommand):
            return self._get_literal(command, context)
        if isinstance(command, SequenceCommand):
            return self._get_sequence(command, context)
        if isinstance(command, VariantCommand):
            return self._get_variant(command, context)
        if isinstance(command, WildcardCommand):
            return self._get_wildcard(command, context)
        if isinstance(command, VariableAssignmentCommand):
            raise NotImplementedError(
                "VariableAssignmentCommand should never be sampled",
            )
        if isinstance(command, VariableAccessCommand):
            return self._get_variable(command, context)
        if isinstance(command, WrapCommand):
            return self._get_wrap(command, context)
        return self._unsupported_command(command)

    def _unsupported_command(self, command: Command) -> ResultGen:
        raise NotImplementedError(
            f"{self.__class__.__name__} does not support {command.__class__.__name__}",
        )

    def _get_wildcard(
        self,
        command: WildcardCommand,
        context: SamplingContext,
    ) -> ResultGen:
        return self._unsupported_command(command)

    def _get_variant(
        self,
        command: VariantCommand,
        context: SamplingContext,
    ) -> ResultGen:
        return self._unsupported_command(command)

    def _get_variant_wildcard_to_variant(
        self,
        command: VariantCommand,
        wildcard_command: WildcardCommand,
        context: SamplingContext,
    ) -> ResultGen:
        """
        将通配符命令转换为变体命令的内部实现方法

        Args:
            command (VariantCommand): 变体命令对象，包含最小/最大边界等参数
            wildcard_command (WildcardCommand): 通配符命令对象
            context (SamplingContext): 采样上下文信息

        Returns:
            ResultGen: 生成的变体结果迭代器

        Note:
            此方法是 _get_variant 的内部辅助方法
        """

        # 修正变量作用域问题，确保通配符内部的变量可以正确访问
        # 參考 test_fn_var_should_work_a01
        context = context.with_variables(wildcard_command.variables)

        wildcard_variant = wildcard_to_variant(
            wildcard_command,
            context=context,
            min_bound=command.min_bound,
            max_bound=command.max_bound,
            separator=command.separator,
        )
        return self._get_variant(wildcard_variant, context)

    def _get_sequence(
        self,
        command: SequenceCommand,
        context: SamplingContext,
    ) -> ResultGen:
        tokens, context = context.process_variable_assignments(command.tokens)
        sub_generators = [context.generator_from_command(c) for c in tokens]

        while True:
            yield rotate_and_join(sub_generators, separator=command.separator)

    def _get_literal(
        self,
        command: LiteralCommand,
        context: SamplingContext,
    ) -> ResultGen:
        while True:
            yield SamplingResult(text=command.literal)

    def _get_variable(
        self,
        command: VariableAccessCommand,
        context: SamplingContext,
    ) -> ResultGen:
        variable = command.name

        command_to_sample = context.immediate_variables.get(variable, None)
        if command_to_sample is None:
            command_to_sample = context.variables.get(variable, command.default)
        if not command_to_sample:
            if context.unknown_variable_value is None:
                raise KeyError(f"Variable {variable} is not defined in this context")
            elif isinstance(context.unknown_variable_value, str):
                command_to_sample = LiteralCommand(context.unknown_variable_value)
            else:
                command_to_sample = context.unknown_variable_value
        return context.for_sampling_variable(variable).generator_from_command(
            command_to_sample,
        )

    def _get_wrap(
        self,
        command: WrapCommand,
        context: SamplingContext,
    ) -> ResultGen:
        return self._unsupported_command(command)
