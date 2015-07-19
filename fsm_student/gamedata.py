# -*- coding: utf-8 -*-
"""Game-wide constants.
    
Game Entities
-------------
* CASTLE_WALL
* ATTACKER
# DEFENDER
       
Message Types
-------------
* LADDER_PLACED: Sent when attackers successfully place a ladder.
* LADDER_DOWN: Sent when defenders successfully knock down a ladder.
* LOOK_FOR_SPACE: Attacker should find an empty space to place a ladder.
"""

# Fake enumeratation of game entities, must start at 1
CASTLE_WALL, ATTACKER, DEFENDER = range(1, 3+1)

# Castle wall data
WALL_MAX = 8
LADDER_HEIGHT = 3

# Fake enumeration of message types
LADDER_PLACED, LADDER_DOWN, LOOK_FOR_SPACE = range(3)

# Victory conditions
WINNING_SCORES = {'ATTACKERS': 5, 'DEFENDERS': 5}

class GameOver(Exception):
    """Raise this exception to end the game."""
    # TODO: Who won?
    pass