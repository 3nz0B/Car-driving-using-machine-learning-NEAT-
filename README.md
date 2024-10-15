NEAT Car Driving Simulation

This project shows a simulation of cars driving on tracks using NEAT (NeuroEvolution of Augmenting Topologies), an evolutionary algorithm that evolves neural networks over generations. The simulation involves training cars to drive autonomously by selecting the best-performing individuals (species) from each generation and reproducing them with slight modifications in their neural network weights, allowing for continuous learning and adaptation.

Overview

1. Driving.py
- This project uses NEAT to train cars to drive on a pre-defined track.
- Visualization: The cars are represented as rectangles, and what they see (inputs) is the distances to the wall from several angles (represented as purple lines). The outputs of the neural network is wether they go forward/left/right.
- Fitness Evaluation: Fitness is determined by its speed and whether it stays on the track. Cars that perform better in terms of these criteria are more likely to reproduce in futur generations.

2. DrivingApp.py
- Custom Track Drawing: This additional feature allows users to draw their own track for the cars to drive on. By creating tracks of different shapes and complexities, users can experiment with how the trained model adapts to new environments.
- Drawing Mode: The user can select a brush, eraser, or undo to create their desired track layout. Once done, the simulation runs the NEAT algorithm on the custom track to see how quickly the cars can learn to navigate it.

Additional Notes

You can play around with the NEAT configuration file (config-feedforward.txt, which contains parameters for evolving the neural networks) to see how it affects the learning process.
