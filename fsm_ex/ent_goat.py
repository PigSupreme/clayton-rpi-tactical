# -*- coding: utf-8 -*-
"""Goat Entity using simple FSM functionality"""

# for python3 compat
from __future__ import unicode_literals
from __future__ import absolute_import
from __future__ import print_function

from random import randint as randint

from fsm_ex.gamedata import BOB, ELSA, BILLY, GameOver
from fsm_ex.gamedata import SHACK, MINE, BANK, SALOON, YARD, FIELDS
from fsm_ex.gamedata import MINER_HOME, STEW_READY, GOAT_ONE, GOAT_TWO, GOAT_THREE

from fsm_ex.base_entity import BaseEntity

from fsm_ex.state_machine import State, STATE_NONE, StateMachine


class Goat(BaseEntity):
    """An actual goat, not just a placeholder for some non-goat.
    
    Note: The constructor doesn't take any actual args, but this syntax is
    needed to call the __init__ method of the superclass. I'm not sure that
    we need to do so here, but it will be a useful reminder for later.    
    """    

    def __init__(self, *args):
        # Calls BaseEntity.__init__ to set-up basic functionality.
        super(Goat, self).__init__(*args)
        
        # Entities need a name and initial location
        self.name = "Billy the Goat" # Will we also have Billy the Kid?
        self.location = FIELDS
        
        # For later identification, because RAWR MOAR GOATS!!!!
        self.me = BILLY

        # Set up the FSM for this entity
        self.fsm = StateMachine(self)

### Replace ActualGoat with the real initial state below 
### Make sure to keep the empty parentheses after the class name!
        self.fsm.set_state(ActualGoat(), GlobalGoatState(), None)

    def update(self):
        """To be called by the EntityManager each update."""
        # Update the FSM logic, and nothing else for now.
        self.fsm.update()

    def receive_msg(self,message):
        """Used by the EntityManage for basic messaging."""
        # Let the FSM handle any messages
        self.fsm.handle_msg(message)

    def change_location(self,newlocation):
        """Instantaneously teleport to a new location.
        
        Parameters
        ----------
        newlocation: LOCATION_CONSTANT
            Enumerated location, imported from gamedata.py
        """
        self.location = newlocation

class GlobalGoatState(State):
    """Goat State: Global state for goats.

    See Wife/Miner State documentation for what to do here.
    """
    def execute(self,agent):
        ### This is stuff the goat should do each update. If not needed,
        ### delete this method (since BaseEntity provides a default).
        pass

    def on_msg(self,agent,message):
        ### Global message code here. Return True if the message was handled
        ### and False if the message was not handled.
        return False

class ActualGoat(State):
    """Template for a non-global goat state."""

    def enter(self, agent):
        ### Code to run just after we enter this state.        
        pass

    def execute(self, agent):
        ### Code to run when we update...this is just a placeholder.
        if randint(0,2):
            print("%s : * Bleats *" % agent.name)

    def leave(self, agent):
        ### Code to run just before we leave this state
        pass
    
    def on_msg(self, agent, message):
        ### Return True if the message was handled
        ### and False if the message was not handled.
        return False
        