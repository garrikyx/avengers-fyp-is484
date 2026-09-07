"""Shared Pydantic base for telemetry_shared wire-format models.

camelCase on the wire (spec 004/005/007's own convention); Python attributes
stay snake_case via `alias_generator`.
"""

from __future__ import annotations

from pydantic import BaseModel, ConfigDict
from pydantic.alias_generators import to_camel


class CamelModel(BaseModel):
    model_config = ConfigDict(
        alias_generator=to_camel, populate_by_name=True, frozen=True, extra="forbid"
    )
