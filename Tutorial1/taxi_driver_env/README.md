# Tutorial 1 - Taxi Driver Environment

![pre-commit](https://img.shields.io/badge/pre--commit-enabled-brightgreen?logo=pre-commit)
![License: GPL v3](https://img.shields.io/badge/License-GPLv3-blue.svg)

## Description

Welcome to the taxi driver simulation tutorial! In this tutorial, you will learn how to create your own Gymnasium environment. Gymnasium is a toolkit for developing and comparing reinforcement learning algorithms. Here, we will guide you through the steps to generate a 2D city with roads and various graphical elements, calculate the shortest route between two points, and build a simple physic engine to simulate a car navigating this route.

In another tutorial, we will build the gymnasium agent that will train the car to drive safely between two locations in the city.

### Overview

This tutorial will cover:

* Generating a 2D city: We will use a graph to model the traffic of the city. From this graph, we will generate geometries and various graphical elements to model a 2D city.
* Calculating the Shortest Route: Using graph algorithms, we will calculate the shortest route between two points on the city.
* Physic Engine: Based on a simple Euler integration, we will build a physic engimne to simulate a car driving experience.

### Prerequisites

To follow along with this tutorial, you should have a basic understanding of:

* Python programming
* Graph theory and algorithms
* Basic Physic concepts

### Tools and Libraries

We will be using the following tools and libraries:

* Python: For implementing the algorithms and reinforcement learning logic.
* raylib: A simple and easy-to-use library to render the 2D city and graphical elements.
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

#### Generating a 2D city

We will create a function to generate a 2D city. The city will be randomly generated but will always produce the same result for a given seed, ensuring reproducibility. The city will include various graphical elements such as:

* 2 lanes roads
* Markings
* Houses
* Trees

#### Calculating the Shortest Route

Using graph theory, we will calculate the shortest route between two points on the map. This involves:

* Representing the city as a graph
* Implementing algorithms such as Dijkstra's or BFS to find the shortest path

#### Implementing Physic Engine

We will implement a simple physic engine to simulate a driving experience. This involves:

* Defining the forces acting on the car
* Implementing the 2nd Newton law: F = ma
* Integrating the result to solve velocity and position calculation.
* Implementing collision detections

#### Rendering the Simulation

Using raylib, we will render the city and visualize the car's journey as it drives on the roads.

#### Conclusion

By the end of this tutorial, you will have a gymnasium environment of a driving car simulation. You will understand how to generate a reproducible 2D city, calculate the shortest route, and simulate a driving car.

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
