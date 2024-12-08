import numpy as np

from taxi_driver_agent.pyflow.core import Layer, Params
from taxi_driver_agent.pyflow.functions import __functions__


class Dense(Layer):
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
        self.activation_prime = __functions__[activation]["prime"]

    def call(self, x: np.ndarray, *args, training: bool = False, **kwargs) -> np.ndarray:
        return self.activation(x @ self.kernel[0] + self.bias[0])

    def backward(self, *args, **kwargs) -> list[np.ndarray]:
        x1, x0, loss = args

        loss = loss * self.activation_prime(x1)
        dw = x0.T @ loss
        db = loss.sum(axis=0, keepdims=True)

        loss = loss @ self.kernel[0].T

        return [dw, db, loss]
