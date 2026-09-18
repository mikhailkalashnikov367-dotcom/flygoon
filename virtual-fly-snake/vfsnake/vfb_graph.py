from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path


@dataclass(frozen=True)
class Edge:
    source: str
    target: str
    weight: float = 1.0
    kind: str = "vfb_synapse"


class VFBGraph:
    def __init__(self, edges: list[Edge], source: str = "unspecified", metadata: dict[str, str] | None = None):
        if not edges:
            raise ValueError("The VFB graph must contain at least one edge")
        self.edges = edges
        self.source = source
        self.metadata = metadata or {}

    @classmethod
    def from_edge_list(cls, path: str | Path) -> "VFBGraph":
        payload = json.loads(Path(path).read_text(encoding="utf-8"))
        raw_edges = payload.get("edges") if isinstance(payload, dict) else payload
        if not isinstance(raw_edges, list):
            raise ValueError("Graph JSON must contain an 'edges' list")
        edges = []
        interface_edges = payload.get("interface_edges", []) if isinstance(payload, dict) else []
        output_names = {"turn_left", "straight", "turn_right"}
        ordered_items = (
            [item for item in interface_edges if item.get("target") not in output_names]
            + raw_edges
            + [item for item in interface_edges if item.get("target") in output_names]
        )
        for index, item in enumerate(ordered_items):
            if not isinstance(item, dict) or not item.get("source") or not item.get("target"):
                raise ValueError(f"Invalid edge at index {index}: source and target are required")
            weight = float(item.get("weight", 1.0))
            if weight != weight or weight == float("inf") or weight == float("-inf"):
                raise ValueError(f"Invalid weight at index {index}")
            kind = str(item.get("kind", "vfb_synapse"))
            if kind not in ("vfb_synapse", "interface"):
                raise ValueError(f"Invalid edge kind at index {index}: {kind}")
            edges.append(Edge(str(item["source"]), str(item["target"]), weight, kind))
        source = str(payload.get("source", "unspecified")) if isinstance(payload, dict) else "unspecified"
        metadata = {key: str(payload[key]) for key in ("dataset", "query", "retrieved", "provenance_url") if key in payload} if isinstance(payload, dict) else {}
        return cls(edges, source, metadata)

    def activate(self, inputs: dict[str, float], outputs: tuple[str, ...]) -> dict[str, float]:
        values = self.propagate(inputs)
        return {name: values.get(name, 0.0) for name in outputs}

    def propagate(self, inputs: dict[str, float]) -> dict[str, float]:
        values = dict(inputs)
        for edge in self.edges:
            values[edge.target] = values.get(edge.target, 0.0) + values.get(edge.source, 0.0) * edge.weight
        return values
