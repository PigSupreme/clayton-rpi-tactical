#!/usr/bin/env python
"""
This is the main exectuable for the westworld2 demo.
"""

# for python3 compat
from __future__ import unicode_literals
from __future__ import absolute_import
from __future__ import print_function

from fsm_ex.gamedata import Characters, Locations, MsgTypes
from fsm_ex.gamedata import GameOver

import logging
logging.basicConfig(format='%(levelname)s: %(message)s', level=logging.DEBUG)

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
        logging.info('GameClock: Time is now %d ticks.', self.gametime)

    def since(self, time):
        """Returns the time elasped on this clock since the given time.
        If negative, time is in the future."""
        return self.gametime - time

##############################################################################

from fsm_ex.base_entity import EntityManager, MessageDispatcher

# TODO: Automate this so that we can just import something from gamedata.py?
# That will be a bit tricky, since each ent_foo.py currently imports from
# gamedata.py, leading to a circular dependency.
from fsm_ex.ent_miner import Miner
from fsm_ex.ent_wife import Wife
from fsm_ex.ent_goat import Goat

BOB, ELSA, BILLY = Characters.BOB, Characters.ELSA, Characters.BILLY
# List of each Character's (EntityID, Class)
CHARACTER_LIST = [(BOB, Miner), (ELSA, Wife), (BILLY, Goat)]

##############################################################################

if __name__ == "__main__":

    # Initialize Manager-type objects:
    MASTER_CLOCK = GameClock()
    ENTITY_MGR = EntityManager()
    MSG_DISPATCHER = MessageDispatcher(MASTER_CLOCK.now, ENTITY_MGR)

    # Create and register entities
    for (ename, etype) in CHARACTER_LIST:
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
