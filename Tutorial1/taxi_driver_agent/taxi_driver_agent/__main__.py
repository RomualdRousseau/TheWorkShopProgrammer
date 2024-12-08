import logging
import os
import time
from typing import Optional

import fire
import gymnasium as gym
import numpy as np
from taxi_driver_env.utils.colorize import colorize
from tqdm import trange

import taxi_driver_agent.pyflow as pf

BATCH_SIZE = 32
BAR_FORMAT = "{l_bar}{bar}| {n_fmt}/{total_fmt}"


class Agent:
    CK = np.array([0.25, 0.5, 0.25])

    def __init__(
        self,
        model: Optional[pf.Sequential] = None,
        mutate: bool = False,
        timestep: int = 0,
    ) -> None:
        self.fitness = 0.0

        lr = pf.functions.lr_exp_decay(timestep, 1000, np.log(0.1), 0.1, 0.001)
        self.model = get_agent_model() if model is None else model.clone()
        self.model.compile(optimizer=pf.optimizers.sgd(momentum=(1 - lr), lr=lr, nesterov=True))

        if mutate:
            self.model.fit(epochs=1, shuffle=False, verbose=False)

    def get_model(self) -> pf.Sequential:
        return self.model

    def get_fitness(self) -> float:
        return self.fitness

    def set_fitness(self, fitness: float) -> pf.GeneticIndividual:
        self.fitness = fitness
        return self

    def get_action(self, observation: dict[str, np.ndarray]) -> np.ndarray:
        vel, cam = observation["agent_vel"], observation["agent_cam"]
        x = np.concat([vel, np.convolve(cam, Agent.CK, "same")])
        y = self.model.predict(x)
        return y[0]


def get_agent_model() -> pf.Sequential:
    return pf.Sequential(
        [
            pf.layers.GeneticDense(17, 32, activation="leaky_relu"),
            pf.layers.GeneticDense(32, 16, activation="leaky_relu"),
            pf.layers.GeneticDense(16, 2, activation="tanh"),
        ],
        trainer=pf.GeneticTrainer(),
    )


def spawn_agents(
    mode: str,
    agent_count: int,
    model_or_pool: Optional[pf.Sequential] | pf.GeneticPool,
    mutate: bool,
    timestep: int = 0,
) -> list[Agent]:
    get_model = lambda: (
        model_or_pool.select_parent().get_model() if isinstance(model_or_pool, pf.GeneticPool) else model_or_pool
    )
    return [
        Agent(get_model(), mutate, timestep)
        for _ in trange(
            agent_count,
            desc=f"Spawning agents ({mode})",
            ncols=80,
            bar_format=BAR_FORMAT,
        )
    ]


def main(
    seed: int = 5,
    mode: str = "training",
    agent_count: int = 100,
    model_file: Optional[str] = None,
    render_fps: Optional[int] = None,
    duration: float = 15.0,
    timestep: int = 0,
) -> None:
    """Welcome to the taxi driver simulation tutorial!

    In this tutorial, you will learn how to create your own Gymnasium agent. Gymnasium is a toolkit for developing and
    comparing reinforcement learning algorithms. Here, we will guide you through the steps to create a machine learning
    model that will train the car in the Taxi Driver Environment to drive safely between 2 locations in the city.

    Params:
    -------
    seed: Initialize the random generators and make the simulation reproductible.
    mode: Set the mode of the simulation; 'training' or 'validation'. 'training" means the model will be trained when
          all agents fail.
    agent_count: Number of agents to run during a training.
    model_file: Load the model file to initialize the agent' networks. AFter a training, the new model will be saved as
                model_file.new
    render_fps: Set the frame per second during a training.
    duration: Duration in minutes of the simulation.
    timestep: Set the starting timestep. It is used to calculate the learning rate.
    """
    assert seed >= 0
    assert mode in ("training", "validation")
    assert mode == "training" or mode == "validation" and model_file is not None
    assert agent_count > 0
    assert render_fps is None or render_fps > 0
    assert duration > 0
    assert timestep >= 0

    if mode == "validation":
        agent_count = 1
        render_fps = 60

    if model_file is not None and os.path.exists(model_file):
        best_model = get_agent_model()
        best_model.load(model_file)
    else:
        best_model = None

    env = gym.make(
        "tutorial1/Tutorial1-v1",
        agent_count=agent_count,
        render_mode="human",
        render_fps=render_fps,
    )

    agents = spawn_agents(mode, agent_count, best_model, False, timestep)
    observation, info = env.reset(seed=seed)

    t_end = time.monotonic() + 60 * duration
    while time.monotonic() < t_end:
        action = [agent.get_action(obs) for agent, obs in zip(agents, observation, strict=True)]

        observation, _, terminated, truncated, info = env.step(action)
        scores, best_agent_vin = info["scores"], info["best_agent_vin"]

        if best_agent_vin >= 0:
            best_model = agents[best_agent_vin].model

        if terminated or truncated:
            logging.warning(
                colorize(
                    "All agents were destroyed, restarting a new time step ...",
                    "yellow",
                )
            )
            timestep += 1

            if mode == "training":
                pool = pf.GeneticPool([agent.set_fitness(score) for agent, score in zip(agents, scores, strict=True)])
                pool.sample()
                pool.normalize()
                agents = spawn_agents(mode, agent_count, pool, True, timestep)

            observation, info = env.reset()

    if mode == "training" and model_file is not None and best_model is not None:
        best_model.save(f"{model_file}.new")

    env.close()


if __name__ == "__main__":
    fire.Fire(main)
