# -*- coding: utf-8 -*-
"""Game-wide constants.
    
Game Entities
-------------
* BOB: Miner Bob, Elsa's husband
* ELSA: Wife Elsa, scourge of wandering goats
       
Locations
---------
* SHACK: Bob and Elsa's humble home
* MINE: Gold mine. Dig for nuggets here!
* BANK: A bank, duh. Deposit nuggets here!
* SALOON: Quench yer thirst here!
* YARD: Frequently invaded by flower-eating goats!

Message Types
-------------
* MINER_HOME: Bob sends this when he comes home from digging.
* STEW_READY: Elsa sends this when she's finished cooking.
"""

# Fake enumeratation of game entities, must start at 1
BOB, ELSA = range(1, 2+1)

# Fake enumeration of locations
SHACK, MINE, BANK, SALOON, YARD = range(5)

# Fake enumeration of message types
MINER_HOME, STEW_READY = range(2)

class GameOver(Exception):
    """Raise this exception to end the game."""
    pass