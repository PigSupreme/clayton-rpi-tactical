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
* FIELDS: Thar be goats in them fields!

Message Types
-------------
* MINER_HOME: Bob sends this when he comes home from digging.
* STEW_READY: Elsa sends this when she's finished cooking.
* GOAT_ONE: Placeholder for some goat-related message.
* GOAT_TWO: Another placeholder....
* GOAT_THREE: And another placeholder....
"""

# Fake enumeratation of game entities, must start at 1
BOB, ELSA, BILLY = range(1, 3+1)

# Fake enumeration of locations
SHACK, MINE, BANK, SALOON, YARD, FIELDS = range(6)

# Fake enumeration of message types
MINER_HOME, STEW_READY, GOAT_ONE, GOAT_TWO, GOAT_THREE = range(5)

class GameOver(Exception):
    """Raise this exception to end the game."""
    pass