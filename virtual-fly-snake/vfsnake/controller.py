from __future__ import annotations

from .vfb_graph import VFBGraph


class VFBController:
    """Maps game features through a reduced, labeled VFB connectivity graph."""

    outputs = ("turn_left", "straight", "turn_right")

    def __init__(self, graph: VFBGraph):
        self.graph = graph

    def preferences(self, observation: tuple[int, ...]) -> tuple[float, float, float]:
        preferences, _ = self.activity(observation)
        return preferences

    def activity(self, observation: tuple[int, ...]) -> tuple[tuple[float, float, float], dict[str, float]]:
        danger_straight, danger_left, danger_right, fruit_straight, fruit_left, fruit_right, _ = observation
        inputs = {
            "danger_front": float(danger_straight),
            "danger_left": float(danger_left),
            "danger_right": float(danger_right),
            "fruit_front": float(fruit_straight),
            "fruit_left": float(fruit_left),
            "fruit_right": float(fruit_right),
        }
        values = self.graph.propagate(inputs)
        return tuple(values.get(name, 0.0) for name in self.outputs), values
