#!/usr/bin/env python
"""
Created on Fri Jun 12 16:57:26 2015

@author: lothar
"""

# for python3 compat
from __future__ import unicode_literals
from __future__ import absolute_import
from __future__ import print_function

from fsm_ex.gamedata import BOB, ELSA, BILLY, GameOver

##############################################################################

class GameClock(object):
    """Class for managing game world clocks/timers."""

    def __init__(self, start=0, tick=1):
        self.gametime = start
        # Tick interval must be positive; default to 1 if not
        if tick > 0:
            self.tick = tick
        else:
            self.tick = 1

    def now(self):
        """Returns the current time on this clock."""
        return self.gametime

    def update(self):
        """Advances the clock by one tick."""
        self.gametime += self.tick

    def since(self, time):
        """Returns the time elasped on this clock since the given time.
        If negative, time is in the future."""
        return self.gametime - time

##############################################################################

from fsm_ex.base_entity import EntityManager, MessageDispatcher

from fsm_ex.ent_miner import Miner
from fsm_ex.ent_wife import Wife
from fsm_ex.ent_goat import Goat

##############################################################################

if __name__ == "__main__":

    # Initialize Manager-type objects:
    MASTER_CLOCK = GameClock() 
    ENTITY_MGR = EntityManager()    
    MSG_DISPATCHER = MessageDispatcher(MASTER_CLOCK.now, ENTITY_MGR)

    # Create and register entities (Miner Bob and Wife Elsa)
    for (ename, etype) in [(BOB, Miner), (ELSA, Wife), (BILLY, Goat)]:
        new_entity = etype(ename,MSG_DISPATCHER)
        ENTITY_MGR.register(new_entity)

    # Start FSM logic: Must be done AFTER all entities are registered.
    ENTITY_MGR.start_all_fsms()

    # Main Loop
    while 1:
        try:
            MASTER_CLOCK.update()
            ENTITY_MGR.update()
            MSG_DISPATCHER.dispatch_delayed()
        except GameOver:
            break

    print("Elapsed time: %d clock ticks." % MASTER_CLOCK.since(0))

