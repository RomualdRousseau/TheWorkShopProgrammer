from __future__ import annotations

import copy
from typing import Callable, Optional, Protocol

import numpy as np
from tqdm import trange

from taxi_driver_agent.pyflow.functions import __functions__


class Trainer(Protocol):
    """This protocol must be implemeted by all trainers to train a model."""

    def train(self, model: Model, x: Optional[np.ndarray], y: Optional[np.ndarray]) -> Optional[np.ndarray]: ...


class Params:
    """This class is responsible for handling parameters with a fixed shape.

    It allows for initialization of parameters,
    supports item setting and retrieval, copying, converting to and from list representations, and checking for
    equality.
    """

    def __init__(
        self,
        shape: tuple[int, int],
        initializer: str = "zeros",
        data: Optional[np.ndarray] = None,
    ) -> None:
        if data is None:
            init_func = __functions__[initializer]["func"]
            data = np.array(
                [
                    init_func(shape[0], shape[1]),
                    np.zeros(shape),
                    np.zeros(shape),
                ]
            )
        self.data = data

    def __getitem__(self, idx: int) -> np.ndarray:
        return self.data[idx]

    def __setitem__(self, idx: int, data: np.ndarray) -> None:
        self.data[idx] = data

    def __eq__(self, other) -> bool:
        if not isinstance(other, Params):
            return NotImplemented
        return np.array_equal(self.data, other.data)

    def apply_grad(self, data: np.ndarray) -> None:
        self[0] += data[0]
        self[1] = data[1]
        self[2] = data[2]

    def clone(self) -> Params:
        shape = (self[0].shape[0], self[0].shape[1])
        return Params(shape, data=self.data.copy())

    def to_list(self) -> list:
        return self[0].tolist()

    def from_list(self, alist: list):
        if len(alist) == 3:  # Old format # noqa: PLR2004
            self.data = np.asarray(alist)
        else:
            self[0] = np.asarray(alist)


class Layer:
    """This is the base class for all layers.

    It provides the structure for storing weights and biases,
    and outlines the necessary methods that every layer should implement or support.
    """

    def __init__(self, kernel: Params, bias: Params, trainable: bool = True) -> None:
        self.kernel = kernel
        self.bias = bias
        self.trainable = trainable

    def call(self, x: np.ndarray, training: bool = False, **kwargs) -> np.ndarray:
        raise NotImplementedError

    def backward(self, *args, **kwargs) -> list[np.ndarray]:
        raise NotImplementedError

    def apply_grad(self, gradient: tuple[np.ndarray, np.ndarray], optimizer_func: Callable) -> Layer:
        if self.trainable:
            self.kernel.apply_grad(optimizer_func(gradient[0], self.kernel[1], self.kernel[2]))
            self.bias.apply_grad(optimizer_func(gradient[1], self.bias[1], self.bias[2]))
        return self

    def clone(self) -> Layer:
        cloned = copy.copy(self)
        cloned.kernel = self.kernel.clone()
        cloned.bias = self.bias.clone()
        return cloned

    def to_dict(self) -> dict[str, list]:
        return {"W": self.kernel.to_list(), "B": self.bias.to_list()}

    def from_dict(self, adict: dict[str, list]) -> None:
        self.kernel.from_list(adict["W"])
        self.bias.from_list(adict["B"])


class Model:
    """This is the base class for all models.

    It provides methods to manage the model's layers, clone the model, load
    model parameters from a file, and save the model to a file.
    """

    def __init__(self, trainer: Trainer):
        self.trainer = trainer

    def call(self, x: np.ndarray, training: bool = False) -> list[np.ndarray]:
        raise NotImplementedError

    def clone(self) -> Model:
        raise NotImplementedError

    def load(self, file_path: str) -> None:
        raise NotImplementedError

    def save(self, file_path: str) -> None:
        raise NotImplementedError

    def compile(self, optimizer: str | Callable = "rmsprop", loss: str = "mse") -> None:
        if isinstance(optimizer, str):
            self.optimizer_func = __functions__[optimizer]["func"]
        else:
            self.optimizer_func = optimizer

        self.loss_func = __functions__[loss]["func"]
        self.loss_prime = __functions__[loss]["prime"]
        self.loss_acc = __functions__[loss]["acc"]

    def fit(
        self,
        x: Optional[np.ndarray] = None,
        y: Optional[np.ndarray] = None,
        epochs: int = 10,
        batch_size: int = 128,
        shuffle: bool = True,
        verbose: bool = True,
    ) -> dict[str, list[float]]:
        history: dict[str, list[float]] = {"loss": [], "accuracy": []}

        n = x.shape[0] if x is not None else 0

        batch_sample = np.arange(n)
        batch_count = max(1, np.ceil(n / batch_size))

        first_pass = True

        for e in range(1, 1 + epochs):
            if verbose:
                print(f"Epoch {e}/{epochs}")

            if shuffle:
                np.random.shuffle(batch_sample)

            train_loss = 0
            train_accuracy = 0

            bar = trange(
                batch_count,
                ncols=120,
                bar_format="{l_bar}{bar}| {n_fmt}/{total_fmt} [{elapsed}<{remaining}{postfix}]",
                disable=not verbose,
            )
            for i in bar:
                sample = batch_sample[i * batch_size : (i + 1) * batch_size]
                loss, accuracy = self.train_batch(x, y, sample)

                if first_pass:
                    first_pass = False
                    history["loss"].append(loss)
                    history["accuracy"].append(accuracy)

                train_loss += loss / batch_count
                train_accuracy += accuracy / batch_count
                bar.set_postfix({"loss": train_loss, "accuracy": train_accuracy})

            history["loss"].append(train_loss)
            history["accuracy"].append(train_accuracy)

        return history

    def evaluate(self, x: np.ndarray, y: np.ndarray, verbose: bool = True) -> tuple[float, float, np.ndarray]:
        """Evaluates the performance of the trained model on a test set."""
        loss, accuracy, yhat = self.test_step(x, y)
        if verbose:
            print(f"Test loss: {loss}")
            print(f"Test accuracy: {accuracy}")
        return loss, accuracy, yhat

    def predict(self, x: np.ndarray) -> np.ndarray:
        """Uses the trained model to make predictions on new data."""
        *_, yhat = self.call(x)
        return yhat

    def train_batch(self, x: Optional[np.ndarray], y: Optional[np.ndarray], sample: np.ndarray) -> tuple[float, float]:
        x_sample = x[sample] if x is not None else x
        y_sample = y[sample] if y is not None else y
        return self.train_step(x_sample, y_sample)

    def train_step(self, x: Optional[np.ndarray], y: Optional[np.ndarray]) -> tuple[float, float]:
        yhat = self.trainer.train(self, x, y)
        loss, accuracy = self.compute_stats(y, yhat)
        return loss, accuracy

    def test_step(self, x: np.ndarray, y: np.ndarray) -> tuple[float, float, np.ndarray]:
        *_, yhat = self.call(x)
        loss, accuracy = self.compute_stats(y, yhat)
        return loss, accuracy, yhat

    def compute_stats(self, y: Optional[np.ndarray], yhat: Optional[np.ndarray]) -> tuple[float, float]:
        if y is None or yhat is None:
            return 0, 0
        return self.loss_func(y, yhat).mean(), self.loss_acc(y, yhat).mean()
