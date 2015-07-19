# -*- coding: utf-8 -*-
"""Sentry Entity using simple FSM functionality.
"""

from __future__ import print_function

from random import randint as roll_int

# Game world constants
from fsm_student.gamedata import WALL_MAX, LADDER_HEIGHT, WINNING_SCORES, GameOver

# Messaging
from fsm_student.gamedata import LADDER_PLACED, LADDER_DOWN, LOOK_FOR_SPACE
from fsm_ex.base_entity import DELAY, SEND_ID, RECV_ID, MSG_TYPE, EXTRA

# Game Entities
from fsm_ex.base_entity import BaseEntity
from fsm_student.gamedata import CASTLE_WALL, ATTACKER, DEFENDER

# State Machines
from fsm_ex.state_machine import State, STATE_NONE, StateMachine

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
        self.fsm.set_state(STATE_NONE, GlobalAttackerState(), None)
        self.fsm.change_state(AttackerWait())

    def update(self):
        self.fsm.update()
        
    def start_climb(self, height=1):
        if self.wall.is_ladder(self.current_ladder):
            self.current_height = 1
            return True
        else:
            return False
        
    def climb(self, rungs=1):
        if self.wall.is_ladder(self.current_ladder):
            self.current_height += rungs
            return True
        else:
            return False
            
    def fall_down(self):
        self.current_ladder = None
        self.current_height = 0
        
        

#######################

class GlobalAttackerState(State):
    """Global state that just handles message.

    Prints that a message was received, with no further details.
    """

    def on_msg(self, agent, message):
        print("%s : A message! Charge!" % agent.name)
        return True
        
#######################
        
class AttackerWait(State):
    """Attackers twiddling their thumbs."""
    
    def enter(self, agent):
        print("%s : Awaiting orders!" % agent.name)
        agent.postoffice.post_msg(roll_int(2,5), ATTACKER, ATTACKER, LOOK_FOR_SPACE)
    
    def on_msg(self, agent, message):
        print("Orders received!")
        if message(MSG_TYPE) == LOOK_FOR_SPACE:
            ladder_loc = agent.wall.get_nearest_ladder(agent.location)
            if ladder_loc is not None:
                agent.current_ladder = ladder_loc
                agent.fsm.change_state(AttackerHoist())
                return True
            else: # No free space for ladder, wait 3 turns...
                agent.postoffice.post_msg(3,ATTACKER,ATTACKER,LOOK_FOR_SPACE)
                return True

#########################

class AttackerHoist(State):
    """Hoist ladder and start climbing..."""

    def execute(self, agent):
        # If ladder is already placed here:
        if agent.wall.is_ladder(agent.current_ladder): 
            d4 = roll_int(1,4)
            if d4 < 3:
                agent.fsm.change_state(AttackerClimb())
            else:
                pass
        # Otherwise, try to place the ladder
        elif agent.wall.place_ladder(agent.current_ladder):
            # TODO: Should the wall post this message instead?            
            agent.postoffice.post_msg(0,ATTACKER,DEFENDER,LADDER_PLACED,agent.current_ladder)
        else:
            agent.fsm.change_state(AttackerWait())
                
#########################
                
class AttackerClimb(State):
    """Climb the ladder at our current space."""
    
    def enter(self, agent):
        if agent.wall.is_ladder(agent.current_ladder):
            agent.start_climb()
             
    def execute(self, agent):
        if agent.wall.is_ladder(agent.current_ladder):
            if agent.climb(1):
                if agent.current_height > LADDER_HEIGHT:
                    agent.wall.score_points('ATTACKERS')
                    # Instead of deleting this attacker, return to WAIT
                    agent.fsm.change_state(AttackerWait())
                else: # Ladder is gone, something went wrong?
                    agent.postoffice.post_msg(0,ATTACKER,ATTACKER,LADDER_DOWN,agent.cuurent_ladder)
                
    def on_msg(self, agent, message):
        """Attackers need to know when their ladder gets knocked down.
        [Added by PigSupreme]
        """
        if message(MSG_TYPE) is LADDER_DOWN:
            ladder_loc = message[EXTRA]
            if agent.current_ladder == ladder_loc:
                agent.fall_down()
                agent.fsm.change_state(AttackerWait())
                return True
        
        return False