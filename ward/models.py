from dataclasses import dataclass
from inspect import BoundArguments
from typing import Optional


@dataclass
class Marker:
    name: str


@dataclass
class SkipMarker(Marker):
    name: str = "SKIP"
    reason: Optional[str] = None


@dataclass
class XfailMarker(Marker):
    name: str = "XFAIL"
    reason: Optional[str] = None


@dataclass
class WardMeta:
    marker: Optional[Marker] = None
    description: Optional[str] = None
    bound_args: Optional[BoundArguments] = None
