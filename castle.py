#!/usr/bin/env python
"""
Student-designed FSM
"""

# for python3 compat
from __future__ import unicode_literals
from __future__ import absolute_import
from __future__ import print_function

from random import randint as roll_int

# Game world constants
from fsm_student.gamedata import WALL_MAX, LADDER_HEIGHT, WINNING_SCORES, MAX_TURNS, GameOver

# Messaging
#from fsm_student.gamedata import LADDER_PLACED, LADDER_DOWN, LOOK_FOR_SPACE
from fsm_ex.base_entity import DELAY, SEND_ID, RECV_ID, MSG_TYPE, EXTRA

# Game Entities
#from fsm_ex.base_entity import BaseEntity
from fsm_student.gamedata import CASTLE_WALL, ATTACKER, DEFENDER

# State Machines
#from fsm_ex.state_machine import State, STATE_NONE, StateMachine

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

from fsm_student.ent_attacker import Attacker
from fsm_student.ent_sentry import Sentry
from fsm_student.ent_wall import Wall

##############################################################################

if __name__ == "__main__":

    # Initialize Manager-type objects:
    MASTER_CLOCK = GameClock()
    ENTITY_MGR = EntityManager()
    MSG_DISPATCHER = MessageDispatcher(MASTER_CLOCK.now, ENTITY_MGR)

    # Create and register entities

    # Wall must be initialized first
    WALLS = Wall(CASTLE_WALL, MSG_DISPATCHER)
    ENTITY_MGR.register(WALLS)

    # Sentries and attackers must be assigned to a wall
    ent_list = [(ATTACKER, Attacker), (DEFENDER, Sentry)]
    for (ename, etype) in ent_list:
        new_entity = etype(ename, MSG_DISPATCHER, WALLS)
        ENTITY_MGR.register(new_entity)

    # Start FSM logic: Must be done AFTER all entities are registered.
    ENTITY_MGR.start_all_fsms()

    # Main Loop
    while MASTER_CLOCK.since(0) < MAX_TURNS:
        try:
            MASTER_CLOCK.update()
            print("\n *** Game Turn %d ***" % MASTER_CLOCK.since(0))
            ENTITY_MGR.update()
            MSG_DISPATCHER.dispatch_delayed()
        except GameOver:
            break

    print("Elapsed time: %d clock ticks." % MASTER_CLOCK.since(0))

