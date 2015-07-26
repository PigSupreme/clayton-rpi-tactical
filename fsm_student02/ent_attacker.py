# -*- coding: utf-8 -*-
"""Sentry Entity using simple FSM functionality.
"""

from __future__ import print_function

# Game world constants
from fsm_student02.gamedata import WALL_MAX, LADDER_HEIGHT, WINNING_SCORES, GameOver

# Messaging
from fsm_student02.gamedata import LOOK_FOR_SPACE as GO_ATTACK
from fsm_student02.gamedata import LADDER_DOWN as KICKED
from fsm_student02.gamedata import LADDER_PLACED as ATTACKED_AT
# LADDER_PLACED, LADDER_DOWN, LOOK_FOR_SPACE
from fsm_ex.base_entity import DELAY, SEND_ID, RECV_ID, MSG_TYPE, EXTRA

# Game Entities
from fsm_ex.base_entity import BaseEntity
from fsm_student02.gamedata import CASTLE_WALL, ATTACKER, DEFENDER

# State Machines
from fsm_ex.state_machine import State, StateMachine

class Attacker(BaseEntity):
    """Comment this class before they breach the walls!!!
    """

    def __init__(self, *args):
        self.wall = args[2]
        args = (args[0], args[1])
        super(Attacker, self).__init__(*args)
        self.name = "Attacker"
        self.current_ladder = None
        self.current_height = 0

        print("%s : Ready for battle!" % self.name)

        # Set up the FSM for this entity
        self.fsm = StateMachine(self)
        self.fsm.set_state(AttackerWait(), GlobalAttackerState(), None)

    def update(self):
        self.fsm.update()

    def receive_msg(self, message):
        # Let the FSM handle any messages
        self.fsm.handle_msg(message)

    def start_climb(self, height=1):
        if self.wall.is_ladder(self.current_ladder):
            self.current_height = 1
            print("%s : Started climbing at space %d." % (self.name, self.current_ladder))
            return True
        else:
            return False

    def climb(self, rungs=1):
        if self.wall.is_ladder(self.current_ladder):
            self.current_height += rungs
            print("%s : Climbing at space %d; height now %d." % (self.name, self.current_ladder, self.current_height))
            return True
        else:
            return False

    def fall_down(self):
        print("%s : Fell from ladder at space %d." % (self.name, self.current_ladder))
        self.current_ladder = None
        self.current_height = 0



#######################

class GlobalAttackerState(State):
    """Global state that just handles message.

    Prints that a message was received, with no further details.
    """

    def on_msg(self, agent, message):
        print("%s : A global message! Charge!" % agent.name)
        return True

#######################

class AttackerWait(State):
    """Attackers twiddling their thumbs."""

    def enter(self, agent):
        print("%s : I'm waiting." % agent.name)
        agent.postoffice.post_msg(3, ATTACKER, ATTACKER, GO_ATTACK)

    def leave(self, agent):
        print("%s : Let's go!" % agent.name)

    def on_msg(self, agent, message):
        if message[MSG_TYPE] == GO_ATTACK:
            agent.fsm.change_state(AttackerHoist())
            return True
        else:
            return False

#########################

class AttackerHoist(State):
    """Hoist ladder and start climbing..."""

    def enter(self, agent):
        print("%s : Looking to place a ladder..." % agent.name)
        ladder_loc = agent.wall.get_empty_ladder_space()
        if ladder_loc is not None:
            agent.current_ladder = ladder_loc
            print("%s : ...there's an empty space at %d." % (agent.name, ladder_loc))
        else: # Not specified, returning to wait state
            print("%s : ...but there are no free spaces." % agent.name)
            agent.fsm.change_state(AttackerWait())

    def execute(self, agent):
        # Try to palce ladder, start climb if successful
        if agent.wall.place_ladder(agent.current_ladder):
            # Added by PigSupreme: Send the ATTACKED_AT message!
            agent.postoffice.post_msg(0, ATTACKER, DEFENDER, ATTACKED_AT, agent.current_ladder)
            agent.fsm.change_state(AttackerClimb())


    def leave(self, agent):
        print("%s : Going up! [AttackerHoist.leave]." % agent.name)

    def on_msg(self, agent, message):
        if message[MSG_TYPE] == KICKED and message[EXTRA] == agent.current_ladder:
            agent.fall_down()
            agent.fsm.change_state(AttackerWait())
            return True
        else:
            return False

#########################

class AttackerClimb(State):
    """Climb the ladder at our current space."""

    def enter(self, agent):
        if agent.wall.is_ladder(agent.current_ladder):
            print("%s : Going up! [AttackerClimb.enter]" % agent.name)
            agent.start_climb()

    def execute(self, agent):
        if agent.wall.is_ladder(agent.current_ladder):
            if agent.climb(1):
                if agent.current_height > LADDER_HEIGHT:
                    print("%s : Made it up the wall! [Added by PigSupreme]" % agent.name)
                    agent.wall.score_points('ATTACKERS')
                    # Instead of deleting this attacker, return to WAIT
                    agent.fsm.change_state(AttackerWait())
            else: # Ladder is gone, something went wrong?
                agent.postoffice.post_msg(0, ATTACKER, ATTACKER, KICKED, agent.current_ladder)

    def on_msg(self, agent, message):
        if message[MSG_TYPE] == KICKED and message[EXTRA] == agent.current_ladder:
            agent.fall_down()
            agent.fsm.change_state(AttackerWait())
            return True
        else:
            return False
