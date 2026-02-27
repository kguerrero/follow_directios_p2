"""Helpers for deriving conversational requirements from Pydantic models."""
from __future__ import annotations

from dataclasses import dataclass
import inspect
from types import UnionType
from typing import Any, Iterable, Literal, Union, get_args, get_origin

from pydantic import BaseModel
from pydantic.fields import PydanticUndefined


@dataclass(frozen=True)
class RequirementLine:
    path: str
    required: bool
    description: str

    @property
    def requirement_label(self) -> str:
        return "required" if self.required else "optional"


def _strip_optional(annotation: Any) -> tuple[Any, bool]:
    origin = get_origin(annotation)
    if origin in (Union, UnionType):
        args = [arg for arg in get_args(annotation) if arg is not type(None)]
        if len(args) == 1:
            return args[0], True
    return annotation, False


def _is_base_model(annotation: Any) -> bool:
    return inspect.isclass(annotation) and issubclass(annotation, BaseModel)


def _is_base_model_collection(annotation: Any) -> bool:
    origin = get_origin(annotation)
    if origin not in (list, set):
        return False
    args = get_args(annotation)
    if not args:
        return False
    return _is_base_model(args[0])


def _annotation_to_text(annotation: Any) -> str:
    origin = get_origin(annotation)
    if origin is None:
        if isinstance(annotation, type):
            return annotation.__name__
        return str(annotation).replace("typing.", "")

    if origin is list:
        inner = _annotation_to_text(get_args(annotation)[0])
        return f"list[{inner}]"
    if origin is set:
        inner = _annotation_to_text(get_args(annotation)[0])
        return f"set[{inner}]"
    if origin in (Union, UnionType):
        return " | ".join(_annotation_to_text(arg) for arg in get_args(annotation))
    if origin is Literal:
        choices = ", ".join(str(arg) for arg in get_args(annotation))
        return f"one of: {choices}"
    return str(annotation).replace("typing.", "")


def _default_suffix(field) -> str | None:
    if field.default_factory not in (None, PydanticUndefined):
        factory_name = getattr(field.default_factory, "__name__", "callable")
        return f"default factory `{factory_name}`"
    if field.default is not PydanticUndefined:
        return f"default {field.default!r}"
    return None


def _describe_model_fields(
    model: type[BaseModel], prefix: str = ""
) -> list[RequirementLine]:
    lines: list[RequirementLine] = []
    for field_name, field in model.model_fields.items():
        annotation, _ = _strip_optional(field.annotation)
        path = f"{prefix}{field_name}"
        type_text = _annotation_to_text(annotation)
        description = field.description or f"{type_text} value"
        default_suffix = _default_suffix(field)
        if default_suffix:
            description = f"{description} ({default_suffix})"
        lines.append(
            RequirementLine(
                path=path,
                required=field.is_required(),
                description=description,
            )
        )

        if _is_base_model(annotation):
            lines.extend(_describe_model_fields(annotation, prefix=f"{path}."))
        elif _is_base_model_collection(annotation):
            nested_model = get_args(annotation)[0]
            lines.extend(_describe_model_fields(nested_model, prefix=f"{path}[]."))

    return lines


def iter_model_requirements(model: type[BaseModel]) -> Iterable[RequirementLine]:
    """Yield requirement lines for the given model."""
    return _describe_model_fields(model)


def format_requirement_section(
    model: type[BaseModel],
    *,
    heading: str | None = None,
    heading_indent: str = "",
    bullet_indent: str = "",
) -> str:
    """Format a textual requirements block for prompts."""
    lines = list(iter_model_requirements(model))
    formatted: list[str] = []
    if heading:
        formatted.append(f"{heading_indent}{heading}")
    for line in lines:
        formatted.append(
            f"{bullet_indent}- {line.path} ({line.requirement_label}): {line.description}"
        )
    return "\n".join(formatted)

