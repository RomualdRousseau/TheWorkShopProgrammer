from gymnasium.envs.registration import register

register(
    id="tutorial1/Tutorial1-v1",
    entry_point="taxi_driver_env.envs:Tutorial1Env",
)
