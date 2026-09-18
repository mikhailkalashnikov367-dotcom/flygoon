from __future__ import annotations

import argparse
import json
import random
import threading
import time
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from urllib.parse import urlparse

from .controller import VFBController
from .game import SnakeGame
from .vfb_graph import VFBGraph


class Simulation:
    def __init__(self, graph_path: str):
        self.graph = VFBGraph.from_edge_list(graph_path)
        self.controller = VFBController(self.graph)
        self.game = SnakeGame(seed=17)
        self.running = False
        self.lock = threading.Lock()
        self.activity: dict[str, float] = {}
        self.last_action = "straight"
        self.last_reward = 0.0
        self.last_event = "ready"
        self.total_reward = 0.0
        self.steps = 0
        self.episodes = 0
        self.q: dict[str, list[float]] = {}
        self.random = random.Random(23)
        self.epsilon = 1.0
        self.learning_rate = 0.18
        self.gamma = 0.9
        self.episode_scores: list[int] = []
        self.speed = 5
        self.execution_trace: list[dict[str, str]] = [
            {"kind": "comment", "text": "# Đang chờ tín hiệu từ mô phỏng..."},
            {"kind": "code", "text": "observation = brain.read_sensors()"},
            {"kind": "code", "text": "action = brain.select_action(observation)"},
            {"kind": "code", "text": "reward = environment.step(action)"},
            {"kind": "code", "text": "brain.learn(observation, action, reward)"},
        ]

    def tick(self) -> None:
        with self.lock:
            if self.game.done:
                self.episode_scores.append(self.game.score)
                self.episode_scores = self.episode_scores[-100:]
                self.episodes += 1
                self.game.reset()
            observation = self.game.observation()
            preferences, activity = self.controller.activity(observation)
            activity = {name: round(value, 3) for name, value in activity.items() if abs(value) > 0.001}
            state_key = ",".join(map(str, observation))
            values = self.q.setdefault(state_key, [0.0, 0.0, 0.0])
            self.epsilon = max(0.05, self.epsilon * 0.9995)
            if self.random.random() < self.epsilon:
                action = self.random.randrange(3)
            else:
                action = max(range(3), key=lambda i: values[i] + preferences[i] * 0.05)
            result = self.game.step(action)
            next_key = ",".join(map(str, result.observation))
            next_values = self.q.setdefault(next_key, [0.0, 0.0, 0.0])
            target = result.reward if result.done else result.reward + self.gamma * max(next_values)
            values[action] += self.learning_rate * (target - values[action])
            self.activity = activity
            self.last_action = self.controller.outputs[action]
            self.last_reward = result.reward
            self.total_reward += result.reward
            self.steps += 1
            self.last_event = "reward_fruit" if result.ate else "punishment_collision" if result.done else "step_cost"
            active_nodes = ", ".join(list(activity)[:3]) or "không có"
            event_name = "ăn quả" if result.ate else "va chạm" if result.done else "di chuyển"
            self.execution_trace = [
                {"kind": "comment", "text": f"# tick {self.steps:04d} · episode {self.episodes} · epsilon={self.epsilon:.3f}"},
                {"kind": "code", "text": f"observation = {observation}"},
                {"kind": "active", "text": f"vfb.activate(nodes=[{active_nodes}])"},
                {"kind": "action", "text": f"action = \"{self.last_action}\"  # Q-learning / epsilon-greedy"},
                {"kind": "reward", "text": f"reward = {result.reward:+.2f}  # {event_name}"},
                {"kind": "learn", "text": f"Q[state, action] += {self.learning_rate:.2f} * (target - Q[state, action])"},
            ]

    def snapshot(self) -> dict:
        with self.lock:
            observation = self.game.observation()
            return {
                "snake": self.game.snake,
                "fruit": self.game.fruit,
                "score": self.game.score,
                "done": self.game.done,
                "running": self.running,
                "action": self.last_action,
                "activity": self.activity,
                "inputs": {
                    "nguy_hiểm_phía_trước": observation[0],
                    "nguy_hiểm_bên trái": observation[1],
                    "nguy_hiểm_bên phải": observation[2],
                    "quả_phía_trước": observation[3],
                    "quả_bên trái": observation[4],
                    "quả_bên phải": observation[5],
                },
                "graph_source": self.graph.source,
                "provenance": self.graph.metadata,
                "node_count": len({name for edge in self.graph.edges for name in (edge.source, edge.target)}),
                "edge_count": len(self.graph.edges),
                "vfb_edge_count": sum(edge.kind == "vfb_synapse" for edge in self.graph.edges),
                "interface_edge_count": sum(edge.kind == "interface" for edge in self.graph.edges),
                "model": "Mô phỏng connectome rút gọn",
                "reward": self.last_reward,
                "total_reward": round(self.total_reward, 2),
                "steps": self.steps,
                "episodes": self.episodes,
                "epsilon": round(self.epsilon, 3),
                "learned_states": len(self.q),
                "average_score": round(sum(self.episode_scores) / len(self.episode_scores), 2) if self.episode_scores else 0,
                "score_history": self.episode_scores[-30:],
                "speed": self.speed,
                "event": self.last_event,
                "data_status": "DEMO GRAPH — chưa phải dữ liệu VFB thật" if self.graph.source.startswith("demo-only") else "VFB SYNAPSE EXPORT — có cạnh giao diện được đánh dấu",
                "execution_trace": self.execution_trace,
                "edges": [{"source": e.source, "target": e.target, "weight": e.weight, "kind": e.kind} for e in self.graph.edges],
            }


def run_simulation(simulation: Simulation) -> None:
    while True:
        if simulation.running:
            for _ in range(simulation.speed):
                simulation.tick()
        time.sleep(0.035)


class Handler(BaseHTTPRequestHandler):
    simulation: Simulation
    root: Path

    def _json(self, value: object, status: int = 200) -> None:
        encoded = json.dumps(value).encode("utf-8")
        self.send_response(status)
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", str(len(encoded)))
        self.end_headers()
        self.wfile.write(encoded)

    def do_GET(self) -> None:
        path = urlparse(self.path).path
        if path == "/api/state":
            self._json(self.simulation.snapshot())
            return
        if path == "/":
            path = "/index.html"
        file_path = (self.root / path.lstrip("/")).resolve()
        if self.root not in file_path.parents or not file_path.is_file():
            self.send_error(404)
            return
        content_type = "text/html; charset=utf-8" if file_path.suffix == ".html" else "text/css; charset=utf-8" if file_path.suffix == ".css" else "text/javascript; charset=utf-8"
        content = file_path.read_bytes()
        self.send_response(200)
        self.send_header("Content-Type", content_type)
        self.send_header("Content-Length", str(len(content)))
        self.end_headers()
        self.wfile.write(content)

    def do_POST(self) -> None:
        path = urlparse(self.path).path
        if path == "/api/simulate":
            self.simulation.running = True
            self._json({"running": True})
        elif path == "/api/pause":
            self.simulation.running = False
            self._json({"running": False})
        elif path == "/api/reset":
            self.simulation.running = False
            with self.simulation.lock:
                self.simulation.game.reset()
                self.simulation.last_reward = 0.0
                self.simulation.last_event = "ready"
                self.simulation.total_reward = 0.0
                self.simulation.steps = 0
                self.simulation.episodes = 0
                self.simulation.q.clear()
                self.simulation.epsilon = 1.0
                self.simulation.episode_scores.clear()
                self.simulation.execution_trace = [
                    {"kind": "comment", "text": "# Đang chờ tín hiệu từ mô phỏng..."},
                    {"kind": "code", "text": "observation = brain.read_sensors()"},
                    {"kind": "code", "text": "action = brain.select_action(observation)"},
                    {"kind": "code", "text": "reward = environment.step(action)"},
                    {"kind": "code", "text": "brain.learn(observation, action, reward)"},
                ]
            self._json({"running": False})
        elif path.startswith("/api/speed/"):
            try:
                speed = int(path.rsplit("/", 1)[1])
            except ValueError:
                self.send_error(400, "Speed must be an integer")
                return
            if speed not in (1, 5, 20):
                self.send_error(400, "Speed must be 1, 5, or 20")
                return
            self.simulation.speed = speed
            self._json({"speed": speed})
        else:
            self.send_error(404)

    def log_message(self, *_args: object) -> None:
        return


def main() -> None:
    parser = argparse.ArgumentParser(description="Run the Virtual Fly Snake browser simulator")
    parser.add_argument("--graph", default="data/vfb_real_subgraph.json")
    parser.add_argument("--port", type=int, default=8765)
    args = parser.parse_args()
    simulation = Simulation(args.graph)
    threading.Thread(target=run_simulation, args=(simulation,), daemon=True).start()
    Handler.simulation = simulation
    Handler.root = Path(__file__).parent.parent / "web"
    server = ThreadingHTTPServer(("127.0.0.1", args.port), Handler)
    print(f"Open http://127.0.0.1:{args.port} in your browser")
    server.serve_forever()


if __name__ == "__main__":
    main()
