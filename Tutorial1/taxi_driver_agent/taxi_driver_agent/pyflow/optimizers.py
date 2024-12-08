from functools import partial

from taxi_driver_agent.pyflow.functions import wu_adadelta, wu_adam, wu_rmsprop, wu_sgd


def sgd(momentum=0.0, lr=0.01, nesterov=False):
    return partial(wu_sgd, momentum=momentum, lr=lr, nesterov=nesterov)


def adatdelta(rho=0.95):
    return partial(wu_adadelta, rho=rho)


def rmsprop(rho=0.9, lr=0.1):
    return partial(wu_rmsprop, rho=rho, lr=lr)


def adam(beta1=0.9, beta2=0.999, lr=0.001):
    return partial(wu_adam, beta1=beta1, beta2=beta2, lr=lr)
