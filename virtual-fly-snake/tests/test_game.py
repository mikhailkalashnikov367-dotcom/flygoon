import unittest

from vfsnake.game import SnakeGame
from vfsnake.vfb_graph import VFBGraph


class GameTests(unittest.TestCase):
    def test_reset_is_deterministic(self):
        first = SnakeGame(seed=4)
        second = SnakeGame(seed=4)
        self.assertEqual(first.observation(), second.observation())
        self.assertEqual(first.fruit, second.fruit)

    def test_fruit_increases_length(self):
        game = SnakeGame(seed=1)
        game.fruit = (game.snake[0][0] + 1, game.snake[0][1])
        result = game.step(1)
        self.assertTrue(result.ate)
        self.assertEqual(len(game.snake), 3)

    def test_graph_activation(self):
        graph = VFBGraph.from_edge_list("data/example_vfb_graph.json")
        values = graph.activate({"fruit_front": 1.0}, ("straight",))
        self.assertEqual(values["straight"], 1.2)


if __name__ == "__main__":
    unittest.main()
