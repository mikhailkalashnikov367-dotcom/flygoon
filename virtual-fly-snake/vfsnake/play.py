from __future__ import annotations

import argparse
import json
import time

import pygame

from .controller import VFBController
from .game import SnakeGame
from .vfb_graph import VFBGraph


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--qtable", default="artifacts/qtable.json")
    parser.add_argument("--graph", default="data/example_vfb_graph.json")
    args = parser.parse_args()
    payload = json.loads(open(args.qtable, encoding="utf-8").read())
    q = payload["q"]
    controller = VFBController(VFBGraph.from_edge_list(args.graph))
    game = SnakeGame()
    pygame.init()
    screen = pygame.display.set_mode((480, 480))
    clock = pygame.time.Clock()
    running = True
    while running:
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False
        observation = game.observation()
        values = q.get(",".join(map(str, observation)), [0.0, 0.0, 0.0])
        bias = controller.preferences(observation)
        action = max(range(3), key=lambda i: values[i] + bias[i])
        game.step(action)
        screen.fill((20, 20, 25))
        for x, y in game.snake:
            pygame.draw.rect(screen, (50, 210, 90), (x * 40, y * 40, 38, 38))
        pygame.draw.rect(screen, (230, 70, 70), (game.fruit[0] * 40, game.fruit[1] * 40, 38, 38))
        pygame.display.flip()
        if game.done:
            time.sleep(0.4)
            game.reset()
        clock.tick(12)
    pygame.quit()


if __name__ == "__main__":
    main()
