from __future__ import annotations

import random
from dataclasses import dataclass

Point = tuple[int, int]
HEADINGS: tuple[Point, ...] = ((0, -1), (1, 0), (0, 1), (-1, 0))


@dataclass
class StepResult:
    observation: tuple[int, ...]
    reward: float
    done: bool
    ate: bool


class SnakeGame:
    def __init__(self, width: int = 12, height: int = 12, seed: int | None = None):
        if width < 5 or height < 5:
            raise ValueError("Board must be at least 5 by 5")
        self.width, self.height = width, height
        self.random = random.Random(seed)
        self.reset()

    def reset(self) -> tuple[int, ...]:
        center = (self.width // 2, self.height // 2)
        self.snake: list[Point] = [center, (center[0] - 1, center[1])]
        self.heading = 1
        self.done = False
        self.score = 0
        self._place_fruit()
        return self.observation()

    def _place_fruit(self) -> None:
        free = [(x, y) for x in range(self.width) for y in range(self.height) if (x, y) not in self.snake]
        self.fruit = self.random.choice(free)

    def _relative(self, turn: int) -> Point:
        direction = HEADINGS[(self.heading + turn) % 4]
        return direction

    def _danger(self, turn: int) -> int:
        dx, dy = self._relative(turn)
        head = self.snake[0]
        point = (head[0] + dx, head[1] + dy)
        return int(point[0] < 0 or point[0] >= self.width or point[1] < 0 or point[1] >= self.height or point in self.snake[:-1])

    def _fruit_direction(self, turn: int) -> int:
        dx, dy = self._relative(turn)
        head = self.snake[0]
        fx, fy = self.fruit
        return int((fx - head[0]) * dx + (fy - head[1]) * dy > 0)

    def observation(self) -> tuple[int, ...]:
        return (self._danger(0), self._danger(-1), self._danger(1), self._fruit_direction(0), self._fruit_direction(-1), self._fruit_direction(1), self.heading)

    def step(self, action: int) -> StepResult:
        if self.done:
            raise RuntimeError("Cannot step a finished game; call reset()")
        if action not in (0, 1, 2):
            raise ValueError("Action must be 0 (left), 1 (straight), or 2 (right)")
        turn = (-1, 0, 1)[action]
        self.heading = (self.heading + turn) % 4
        dx, dy = HEADINGS[self.heading]
        new_head = (self.snake[0][0] + dx, self.snake[0][1] + dy)
        ate = new_head == self.fruit
        collision = new_head[0] < 0 or new_head[0] >= self.width or new_head[1] < 0 or new_head[1] >= self.height or new_head in self.snake[:-1]
        if collision:
            self.done = True
            return StepResult(self.observation(), -10.0, True, False)
        self.snake.insert(0, new_head)
        if ate:
            self.score += 1
            reward = 10.0
            self._place_fruit()
        else:
            self.snake.pop()
            reward = -0.05
        return StepResult(self.observation(), reward, False, ate)
