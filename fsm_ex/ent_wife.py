# -*- coding: utf-8 -*-
"""Wife Entity using simple FSM functionality"""

# for python3 compat
from __future__ import unicode_literals
from __future__ import absolute_import
from __future__ import print_function

from random import randint as randint

from fsm_ex.gamedata import BOB, ELSA, GameOver
from fsm_ex.gamedata import SHACK, MINE, BANK, SALOON, YARD
from fsm_ex.gamedata import MINER_HOME, STEW_READY

from fsm_ex.base_entity import BaseEntity
from fsm_ex.base_entity import DELAY, SEND_ID, RECV_ID, MSG_TYPE, EXTRA

from fsm_ex.state_machine import State, STATE_NONE, StateMachine


class Wife(BaseEntity):
    """Wife Elsa, scourge of the goats.
    
    Note: The constructor doesn't take any actual args, but this syntax is
    needed to call the __init__ method of the superclass. I'm not sure that
    we need to do so here, but it will be a useful reminder for later.    
    """    

    def __init__(self, *args):
        super(Wife, self).__init__(*args)
        self.name = "Wife Elsa"
        self.location = SHACK
        #self.gold = 0
        #self.bank = 0
        #self.thirst = 0
        #self.fatigue = 0

        # Set up the FSM for this entity
        self.fsm = StateMachine(self)
        self.fsm.set_state(STATE_NONE,GlobalWifeState(),None)
        self.fsm.change_state(DoHouseWork())

    def update(self):
        """Updates the FSM logic, and nothing else."""
        self.fsm.update()

    def receive_msg(self,message):
        # Let the FSM handle any messages
        self.fsm.handle_msg(message)

    def change_location(self,newlocation):
        self.location = newlocation

class GlobalWifeState(State):
    """Wife State: Global state that handles messages and chases goats!

    State Transitions (these change the current state, not the global one):

    * Goat in yard -> ChaseGoat
    * on_msg MINER_HOME -> Cook Stew
    """
    def execute(self,agent):
        # If not in the YARD, random chance of goat appearing
        if (agent.location != YARD) and (randint(1,3) == 1):
            agent.fsm.change_state(ChaseGoat())

    def on_msg(self,agent,message):
        if message[MSG_TYPE] == MINER_HOME:
            agent.fsm.change_state(CookStew())
            return True
        else:
            print("%s : Done got me a message, oh my!" % agent.name)
            return False

class DoHouseWork(State):
    """Old West misogyny, yeehaw!

    Note
    ----

    Elsa is apparently a lot tougher than her husband, since she never gets
    tired or thirsty! We should probably give her some more interesting things
    to do...a good exercise in FSM design/coding!

    This state has no transitions; those are handled by GlobalWifeState.
    """

    def enter(self,agent):
        # Housework is done at the SHACK only.
        if agent.location != SHACK:
            print("Headin' on home...")
            agent.change_location(SHACK)
        print("%s : Housework ain't gonna do itself!" % agent.name)

    def execute(self,agent):
        # ...and she sings while doing the housework, obviously.
        if randint(0,2):
            print("%s : Workin' round the house...tra-la-lah-la-lah..." % agent.name)

class CookStew(State):
    """More bro-gramming at it's finest, but the code is quite involved.

    On entering this state, Elsa posts a delayed STEW_READY message so that
    she knows the cooking is done. Once she receives this, she then sends an
    immediate STEW_READY to Bob before sitting down to eat herself.

    State Transitions:

    * on_msg STEW_READY -> WifeEatStew
    """
    def enter(self,agent):
        if agent.location != SHACK:
            print("%s : Heading back to the kitchen..." % agent.name)
        print("%s : Gonna rustle up some mighty fine stew!" % agent.name)
        # Post a message to future self; received when stew is ready
        agent.postoffice.post_msg(randint(3,5),ELSA,ELSA,STEW_READY)

    def execute(self,agent):
        print("%s : Wrassalin' with dinner..." % agent.name)

    def on_msg(self,agent,message):
        if message[MSG_TYPE] == STEW_READY:
            print("%s : Stew's ready, come an' git it!" % agent.name)
            agent.postoffice.post_msg(0,ELSA,BOB,STEW_READY)
            agent.fsm.change_state(WifeEatStew())
            return True
        else:
            return False

class WifeEatStew(State):
    """Eat that tasty stew!

    State Transitions:

    * After one execute() to eat stew -> DoHouseWork
    """
    def enter(self,agent):
        if agent.location != SHACK:
            print("%s : Headin' to the dinner table..." % agent.name)
            agent.change_location(SHACK)

    def execute(self,agent):
        print("%s : Eatin' the stew...I outdone myself this time." % agent.name)
        agent.fsm.change_state(DoHouseWork())

class ChaseGoat(State):
    """Head to the yard and shoo that goat!
    
    Goats are stubborn critters, so there's a random chance that Elsa fails
    to shoo the goat. But she'll keep at it until the job's done! 
    
    Goats also demand undivided attention, but Elsa has a good memory. Any
    message received by this state will be forwarded to Elsa in the next
    update() cycle. This means that if Bob comes home whilst Elsa's chasing a
    goat, she'll still receive the MINER_HOME message when she's done.
    
    State Transitions:
    
    * Successfully shoos the goat -> revert to previous
    """
    def enter(self,agent):
        # If not already in the yard, move there and chase that goat!
        if agent.location != YARD:
            print("%s : Thar's a goat in mah yard!" % agent.name)
            agent.change_location(YARD)

    def execute(self, agent):
        print("%s : Shoo, ya silly goat!" % agent.name)
        # Random chance the goat will listen. Goats are stubborn
        if randint(0,2):
            print("Goat : *Nom nom flowers*")
        else:
            print("Goat : *Scampers away*")
            agent.fsm.revert_state()

    def on_msg(self,agent,message):
        #Busy chasing the goat, so forward messages to future self.
        delay, send_id, rec_id, msg_type, extra = message
        agent.postoffice.post_msg(1, send_id, rec_id, msg_type, extra)
        return True
