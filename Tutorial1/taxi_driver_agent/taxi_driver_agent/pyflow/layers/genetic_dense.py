import numpy as np

from taxi_driver_agent.pyflow.core import Layer, Params
from taxi_driver_agent.pyflow.functions import __functions__


class GeneticDense(Layer):
    def __init__(
        self,
        inputs: int,
        outputs: int,
        activation: str = "linear",
        kernel_initializer: str = "gorot",
        bias_initializer: str = "zeros",
    ):
        super().__init__(
            Params((inputs, outputs), initializer=kernel_initializer),
            Params((1, outputs), initializer=bias_initializer),
        )
        self.activation = __functions__[activation]["func"]

    def call(self, x: np.ndarray, *args, training: bool = False, **kwargs) -> np.ndarray:
        return self.activation(x @ self.kernel[0] + self.bias[0])

    def backward(self, *args, **kwargs) -> list[np.ndarray]:
        rate, variance = args

        rate_mask = np.where(np.random.random_sample(self.kernel[0].shape) < rate, 1, 0)
        dw = np.random.standard_normal(self.kernel[0].shape) * rate_mask * variance

        rate_mask = np.where(np.random.random_sample(self.bias[0].shape) < rate, 1, 0)
        db = np.random.standard_normal(self.bias[0].shape) * rate_mask * variance

        return [dw, db]
