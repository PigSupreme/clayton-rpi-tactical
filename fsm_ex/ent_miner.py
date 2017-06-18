# -*- coding: utf-8 -*-
"""Miner Entity using simple FSM functionality.
"""

# for python3 compat
from __future__ import unicode_literals
from __future__ import absolute_import
from __future__ import print_function

from random import randint

from fsm_ex.base_entity import BaseEntity
from fsm_ex.state_machine import State, STATE_NONE, StateMachine
from fsm_ex.gamedata import Characters, Locations, MsgTypes
from fsm_ex.gamedata import GameOver


class Miner(BaseEntity):
    """Miner Bob.

    Note: The constructor doesn't take any actual args, but this syntax is
    needed to call the __init__ method of the superclass. I'm not sure that
    we need to do so here, but it will be a useful reminder for later.
    """

    def __init__(self, *args):
        super(Miner, self).__init__(*args)
        self.name = "Miner Bob"
        self.location = Locations.SHACK
        self.gold = 0
        self.bank = 0
        self.thirst = 0
        self.fatigue = 0

        # For later identification, if we add additional Wives/Miners
        self.me = Characters.BOB
        self.spouse = Characters.ELSA

        # Set up the FSM for this entity
        self.fsm = StateMachine(self)
        self.fsm.set_state(DigInMine(),GlobalMinerState(),None)

    def update(self):
        """Increases thirst and updates the FSM logic."""
        self.thirst += 1
        self.fsm.update()

    def receive_msg(self,message):
        # print("%s: Got me a message of type %d!" % (self.name,msg_type))
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

    def change_gold(self,amount):
        """Add/subtract the amount of gold currently carried

        Parameters
        ----------
        amount: int
            Amount of gold to add (or subtract, if negative)
        """
        self.gold += amount
        #print("[[%s]] : Now carrying %d gold nuggets." % (self.name, self.gold))

    def pockets_full(self):
        """Queries whether this entity is carrying enough gold."""
        return (self.gold >= 3)

    def add_fatigue(self,amount=1):
        """Increases the current fatigue of this entity."""
        self.fatigue += amount
        #print("[[%s]] : Now at fatigue level %d." % (self.name,self.fatigue))

    def remove_fatigue(self,amount=1):
        """Remove fatigue from this entity, but not below zero."""
        self.fatigue -= amount
        if self.fatigue < 0:
            self.fatigue = 0

    def is_thirsty(self):
        """Queries if this entity has too much current thirst."""
        return (self.thirst > 7)

    def remove_thirst(self,amount):
        """Remove thirst from this entity, but not below zero."""
        self.thirst -= amount
        if self.thirst < 0:
            self.thirst = 0

    def work_done(self):
        """Returns True if more than 10 gold in the bank.

        Note
        ----
        Fix this! Once there is 10 gold or more in the bank, the Miner
        will go home after each bank deposit. We don't want that.
        """
        return (self.bank >= 10)

class GlobalMinerState(State):
    """Global state that just handles message.

    Prints that a message was received, with no further details.
    """

    def on_msg(self,agent,message):
        print("%s : Done got me a message! Yeehaw!" % agent.name)
        return True


class DigInMine(State):
    """Go to the mine and dig until pockets full or thirsty.

    State Transitions:

    * When pockets are full -> DepositInBank
    * When thirsty -> DrinkAtSaloon
    """

    def enter(self,agent):
        # If agent is not already in the mine, travel there.
        if agent.location != Locations.MINE:
            print("%s : Walkin' to the gold mine..." % agent.name)
            agent.change_location(Locations.MINE)

    def execute(self,agent):
        # Increase fatigue from digging
        agent.add_fatigue(1)

        # Dig for gold
        gfound = randint(0,2)
        msg = [
            "Keep on a-diggin'...",
            "Found me a gold nugget!",
            "Found me two nuggets, whaddaya know!"
            ][gfound]
        print("%s : %s " % (agent.name,msg))
        agent.change_gold(gfound)

        # If pockets are full, go visit the bank
        if agent.pockets_full():
            agent.fsm.change_state(DepositInBank())
            return # So that we don't try another state change below

        # If thirsty, go visit the saloon
        if agent.is_thirsty():
            agent.fsm.change_state(DrinkAtSaloon())
            return

    def leave(self,agent):
        print("%s : Done diggin' fer now." % agent.name)

class DepositInBank(State):
    """Go to the bank and deposit all carried gold.

    State Transitions:

    * If more than 25 gold in the bank -> GameOver
    * If work_done (enough money in bank) -> GoHomeAndRest
    * Otherwise -> DigInMine
    """

    def enter(self,agent):
        # If agent is not at the bank, travel there.
        if agent.location != Locations.BANK:
            print("%s : Headin' to bank, yessiree!" % agent.name)
            agent.change_location(Locations.BANK)

    def execute(self,agent):
        # Deposit all the gold being carried
        deposit = agent.gold
        if deposit > 0:
            print("%s : Now depositin' %d gold..." % (agent.name,deposit))
            agent.change_gold(-deposit)
            agent.bank += deposit
            print("%s : Saved myself %d gold...soon'll be rich!" % (agent.name,agent.bank))
            if agent.bank > 25:
                print("%s : Whee, doggy! A winner is y'all!" % agent.name)
                raise GameOver

        # If wealthy enough, go home and sleep
        if agent.work_done():
            agent.fsm.change_state(GoHomeAndRest())
            return

        # Otherwise, back to work!
        agent.fsm.change_state(DigInMine())

    def leave(self,agent):
        print("%s : Leavin' the bank..." % agent.name)

class DrinkAtSaloon(State):
    """Go to the saloon and drink until thirst is quenched

    State Transitions:

    * When no longer thirsty -> revert to previous
    """
    def enter(self,agent):
        # If not already at SALOON, go there
        if agent.location != Locations.SALOON:
            print("%s : Headin' to the saloon fer a drink..." % agent.name)
            agent.change_location(Locations.SALOON)

    def execute(self,agent):
        # Have a drink
        print("%s : Havin' a whiskey...mighty refreshin'!" % agent.name)
        agent.remove_thirst(5)

        # If no longer thirsty, go back to whatever we were doin'
        if not agent.is_thirsty():
            agent.fsm.revert_state()
            return

    def leave(self,agent):
        print("%s : Leavin' the saloon fer now..." % agent.name)

class GoHomeAndRest(State):
    """Go home and rest.

    When Miner Bob enters this state, he sends Elsa a message to start cooking
    the stew. He's apparently impatient or a workaholic, because he will go
    back to the mine once fully rested, even if he's not eaten yet. Poor Elsa!

    State Transitions:

    * Once fully rested -> DigInMine
    * If stew is ready and is still in SHACK -> MinerEatStew
    """

    def enter(self,agent):
        # If not at SHACK, go there and tell the wife we're home
        if agent.location != Locations.SHACK:
            print("%s : Day's a finished, headin' on home!" % agent.name)
            agent.change_location(Locations.SHACK)
            agent.postoffice.post_msg(0,agent.get_id(), agent.spouse, MsgTypes.MINER_HOME)

    def execute(self,agent):
        # Take a nap if not fully rested
        if agent.fatigue > 0:
            print("%s : Zzzzzz...." % agent.name)
            agent.remove_fatigue(1)
        else:
            print("%s : Done restin' fer now, back to work!" % agent.name)
            agent.fsm.change_state(DigInMine())

    def on_msg(self,agent,message):
        # If stew's ready, wake up and eat
        if message.MSG_TYPE == MsgTypes.STEW_READY and agent.location == Locations.SHACK:
            print("%s : I hears ya', lil' lady..." % agent.name)
            agent.fsm.change_state(MinerEatStew())
            return True

class MinerEatStew(State):
    """Eat that tasty stew, and thank yer lovely wife!

    Food removes fatigue, of course.

    State Transitions:

    * After a single execute() to eat stew -> revert to previous
    """
    def enter(self,agent):
        if agent.location != Locations.SHACK:
            print("%s : Better git home fer dinner..." % agent.name)
            agent.change_location(Locations.SHACK)

    def execute(self,agent):
        print("%s : That's some might fine stew...thank ya much, Elsa!" % agent.name)
        agent.remove_fatigue(4)
        agent.fsm.revert_state()

    def leave(self,agent):
        print("%s : Now where was I...?" % agent.name)
