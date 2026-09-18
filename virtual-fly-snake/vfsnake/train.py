from __future__ import annotations

import argparse
import json
import random
from pathlib import Path

from .controller import VFBController
from .game import SnakeGame
from .vfb_graph import VFBGraph


def state_key(observation: tuple[int, ...]) -> str:
    return ",".join(map(str, observation))


def train(episodes: int, graph_path: str, seed: int, output: str) -> None:
    randomizer = random.Random(seed)
    graph = VFBGraph.from_edge_list(graph_path)
    controller = VFBController(graph)
    q: dict[str, list[float]] = {}
    scores: list[int] = []
    for episode in range(episodes):
        game = SnakeGame(seed=seed + episode)
        observation = game.reset()
        total = 0.0
        epsilon = max(0.05, 1.0 - episode / max(1, episodes * 0.8))
        for _ in range(600):
            key = state_key(observation)
            values = q.setdefault(key, [0.0, 0.0, 0.0])
            if randomizer.random() < epsilon:
                action = randomizer.randrange(3)
            else:
                bias = controller.preferences(observation)
                action = max(range(3), key=lambda index: values[index] + bias[index])
            result = game.step(action)
            next_values = q.setdefault(state_key(result.observation), [0.0, 0.0, 0.0])
            target = result.reward if result.done else result.reward + 0.9 * max(next_values)
            values[action] += 0.15 * (target - values[action])
            total += result.reward
            observation = result.observation
            if result.done:
                break
        scores.append(game.score)
        if (episode + 1) % max(1, episodes // 10) == 0:
            print(f"episode={episode + 1} score={game.score} reward={total:.2f} epsilon={epsilon:.3f}")
    destination = Path(output)
    destination.parent.mkdir(parents=True, exist_ok=True)
    destination.write_text(json.dumps({"graph_source": graph.source, "q": q}, indent=2), encoding="utf-8")
    print(f"saved {destination} | final_mean_score={sum(scores[-100:]) / min(100, len(scores)):.2f}")


def main() -> None:
    parser = argparse.ArgumentParser(description="Train the VFB-inspired Snake controller")
    parser.add_argument("--episodes", type=int, default=5000)
    parser.add_argument("--graph", default="data/example_vfb_graph.json")
    parser.add_argument("--seed", type=int, default=7)
    parser.add_argument("--output", default="artifacts/qtable.json")
    args = parser.parse_args()
    train(args.episodes, args.graph, args.seed, args.output)


if __name__ == "__main__":
    main()
