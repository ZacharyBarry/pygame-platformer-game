# Retro Platformer Adventure

A 2D retro-style platformer game built entirely in Python using the Pygame library. Players must navigate through 10 progressively challenging, seasonal-themed levels—from lush spring grass to frozen winter ice—dodging hazards and utilizing physics-based movement to reach the golden goal.

## Features

* **10 Unique Levels:** Journey through Early Spring, Summer Heat, Autumn Gold, and Deep Winter.
* **Advanced Player Mechanics:** Features running, jumping, and a dodge-roll ability with invincibility frames.
* **Dynamic Environment Physics:** Ground movement relies on standard platformer physics, while winter levels feature slippery ice physics that carry momentum and require careful friction management.
* **Health System:** Start with 3 hearts. Taking damage from hazards triggers screen-flickering invincibility frames. 
* **Two Game Modes:** Toggle between "normal" mode (restart the current level on death) and "hardcore" mode (permadeath, restart from Level 1) in `game.py`.

## Prerequisites

* Python 3.x
* Pygame library

## Installation & Setup

1. Clone this repository or download the source code to your local machine.
2. Install the required Pygame dependency using pip:
   ```bash
   pip install pygame
