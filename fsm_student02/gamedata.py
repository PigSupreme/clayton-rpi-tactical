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

# for python3 compat
from __future__ import unicode_literals
from __future__ import absolute_import
from __future__ import print_function

# Fake enumeratation of game entities, must start at 1
CASTLE_WALL, ATTACKER, DEFENDER = range(1, 3+1)

# Castle wall data
WALL_MAX = 12
LADDER_HEIGHT = 2

# Fake enumeration of message types
LADDER_PLACED, LADDER_DOWN, LOOK_FOR_SPACE = range(3)

# Victory conditions
WINNING_SCORES = {'ATTACKERS': 5, 'DEFENDERS': 5}
MAX_TURNS = 100

class GameOver(Exception):
    """Raise this exception to end the game."""
    def __init__(self, winning_team, final_scores):
        super(GameOver, self).__init__()
        print("\n *** GAME OVER ***")
        print("Winning team was %s." % str(winning_team))
        print("Final scores:")
        for team, score in final_scores.items():
            print("  %s: %d" % (team, score))
