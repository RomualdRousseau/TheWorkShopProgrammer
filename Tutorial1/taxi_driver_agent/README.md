# Tutorial 1 - Taxi Driver Agent

![License: GPL v3](https://img.shields.io/badge/License-GPLv3-blue.svg)

## Description

Welcome to the taxi driver simulation tutorial! In this tutorial, you will learn how to create your own Gymnasium agent. Gymnasium is a toolkit for developing and comparing reinforcement learning algorithms. Here, we will guide you through the steps to create a machine learning model that will train the car in the Taxi Driver Environment to drive safely between 2 locations in the city.

In another tutorial, we will build the gymnasium environment that will simulate the phycic of the car and visualize the result in a randomly generated city.

### Overview

This tutorial will cover:

* Creating a machine learning model: We will use a "from scratch" approach creating a mini ML engine covering networks of dense layers, activation functions, basic convolution, gradient descent and genetic optimization to train the network ...
* Creating reinforcement learning "agent-environment loop": We will see how a reward approach help to optimize the ML network and see how the car learns to drive. We will experiement several approach: Genetic and Markov decision process

### Prerequisites

To follow along with this tutorial, you should have a basic understanding of:

* Python programming
* Basic Machine Learning concepts

### Tools and Libraries

We will be using the following tools and libraries:

* Python: For implementing the algorithms and reinforcement learning logic.
* Gymansium: A toolkit for developing and comparing reinforcement learning algorithms.

## Getting Started

### Dependencies

* Python 3.11 or above: [python.org](https://python.org/)
* Poetry 1.6.1 or above: [python-poetry.org](https://python-poetry.org/)
* Just 1.28.0 or above: [just.systems](https://just.systems/)

### Install and setup locally

Run the following command line:

```bash
just install
```

### Run the tutorial

Run the following command line:

```bash
just run
```

### Display the coverage report

Run the following command line:

```bash
just coverage
```

### Documentation

#### Creating the Machine Learning model

#### Creating the Agent-Environment Loop

#### Implementing Physic Engine

We will implement a simple physic engine to simulate a driving experience. This involves:

* Defining the forces acting on the car
* Implementing the 2nd Newton law: F = ma
* Integrating the result to solve velocity and position calculation.
* Implementing collision detections


#### Conclusion

By the end of this tutorial, you will have a gymnasium agent of a driving car simulation. You will understand how to model a algorithm to train a car to drive safely between two lcoations.

Feel free to experiment with different seeds, and algorithms to see how they affect the car's performance.

Happy coding and enjoy your self-driving car simulation experience!

## Contribute

Pull requests are welcome. For major changes, please open an issue first to discuss what you would like to change.

Please make sure to update tests as appropriate.

## Authors

* Romuald Rousseau, romualdrousseau@gmail.com

## Version History

* 0.1.0
* Initial Release
