from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

Point = tuple[float, float]


@dataclass
class GraphicObject:
    object_id: str
    name: str
    kind: str
    points: list[Point]
    outline: str = "#000000"
    fill: str = ""
    width: int = 3
    closed: bool = True
    extra: dict[str, Any] = field(default_factory=dict)

    def copy(self) -> "GraphicObject":
        return GraphicObject.from_dict(self.to_dict())

    def to_dict(self) -> dict[str, Any]:
        return {
            "object_id": self.object_id,
            "name": self.name,
            "kind": self.kind,
            "points": [(float(x), float(y)) for x, y in self.points],
            "outline": self.outline,
            "fill": self.fill,
            "width": int(self.width),
            "closed": bool(self.closed),
            "extra": dict(self.extra),
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "GraphicObject":
        return cls(
            object_id=str(data["object_id"]),
            name=str(data["name"]),
            kind=str(data["kind"]),
            points=[(float(x), float(y)) for x, y in data["points"]],
            outline=str(data.get("outline", "#000000")),
            fill=str(data.get("fill", "")),
            width=int(data.get("width", 3)),
            closed=bool(data.get("closed", True)),
            extra=dict(data.get("extra", {})),
        )
