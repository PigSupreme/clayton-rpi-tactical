# -*- coding: utf-8 -*-
"""Miner Entity using simple FSM functionality.
"""

# for python3 compat
from __future__ import unicode_literals
from __future__ import absolute_import
from __future__ import print_function

import logging

from fsm_ex.base_entity import BaseEntity
from fsm_ex.state_machine import State, STATE_NONE, StateMachine

FATIGUE_THRESHOLD = 5000
FATIGUE_RECOVER_RATE = 5
SLEEP_DECEL = 5

HUNGER_THRESHOLD = 2000
EAT_RADIUS_SQ = 20**2

# Higher values will prioritize going home over sleeping
GOHOME_URGENCY = 100

UPDATE_SPEED = 0.1

class InitialFishState(State):
    """Dummy initial state for first update cycle."""

    def execute(self, agent):
        agent.hunger = 0
        agent.fatigue = 0
        agent.steering.set_target(AVOID=agent.obs, WALLAVOID=[30, agent.walls])
        agent.fsm.change_state(SwimState())

class GlobalFishState(State):

    # No enter method here; use initial state instead

    def execute(self, agent):
        # Steering/Physics update
        agent.move(UPDATE_SPEED)

        # TODO: Update agent.maxspeed based on hunger/fatigue

        agent.fatigue += 1
        agent.hunger += 1
        # Fatigue check (make this periodic rather than each update??)
        if agent.fatigue > FATIGUE_THRESHOLD:
            agent.fsm.handle_msg('TIRED')
        else:
            # Hunger has lower priority than sleep
            if agent.hunger > HUNGER_THRESHOLD:
                agent.fsm.handle_msg('HUNGRY')

    def on_msg(self, agent, msg):
        if msg == 'TIRED' and agent.fatigue > FATIGUE_THRESHOLD:
            agent.fsm.change_state(GoHomeState())
            return True
        if msg == 'HUNGRY' and agent.hunger > HUNGER_THRESHOLD:
            agent.fsm.change_state(HuntState())
            return True
        # SHARK_NEAR -> EvadeState
        return False


class SwimState(State):
    """Default state."""

    def enter(self, agent):
        # Activate WANDER
        agent.steering.set_target(WANDER=(90, 15, 3))
        logging.info('Fatigue = %d, Hunger = %d' % (agent.fatigue, agent.hunger))

    def execute(self, agent):
        # TODO: Flocking here
        pass

    def leave(self, agent):
        # Stop WANDER
        agent.steering.stop('WANDER')


class EatState(State):
    """Gateway state for consuming food."""

    def enter(self, agent):
        pass

    def execute(self, agent):
        # Food was eaten before transition, just reset hunger
        agent.hunger = 0
        agent.fsm.change_state(SwimState())

    def on_msg(self, agent, msg):
        # Willfully ignore all messages except for SHARK
        if msg == 'SHARK':
            return False # and thus pass up to global state
        return True


class HuntState(State):
    """Find food and go to it."""

    def enter(self, agent):
        # TODO: This is temporary; get a random food source
        agent.food_pos = agent.feeder.nearest_food_pos(agent.pos)
        logging.info('Fish: HUNGRY ({}), Hunting food at ({:.0f}, {:.0f})'.format(agent.hunger, *agent.food_pos.ntuple()[:]))
        # Determine best available food

        # activate SEEK (to food)
        agent.steering.set_target(SEEK=agent.food_pos)

    def execute(self, agent):
        # TODO: Check current food target
        # Try eating a nearby food
        if agent.feeder.chomp(agent):
            agent.fsm.change_state(EatState())

    def leave(self, agent):
        # stop SEEK (to food)
        agent.food_pos = None
        agent.steering.stop('SEEK')

    def on_msg(self, agent, msg):
        # FOOD_NEAR -> EatState
        pass


#class EvadeState(State):
#    """Get away from the shark."""
#
#    def enter(self, agent):
#        # stop all but AVOID
#        # if shark is close
#        #   activate EVADE
#        #   activate TAKE_COVER
#
#    def execute(self, agent):
#        # check shark distance
#        # near -> EVADE
#        # midrange -> TAKE_COVER
#        # far -> StateSwim
#
#    def leave(self, agent):
#        # deactivate EVADE/TAKE_COVER
#
#    def on_msg(self, agent, msg):
#        # Willfully ignore SHARK
#        # (o/w passed to global)
#
class SleepState(State):
    """Sleeping until fully rested."""

    def enter(self, agent):
        # Deactivate all steering
        # Activate ARRIVE (just ahead of us)
        target = agent.pos + agent.vel.scm(SLEEP_DECEL)
        agent.steering.set_target(ARRIVE=target)

    def execute(self, agent):
        # Gradually reduce fatigue
        agent.fatigue -= FATIGUE_RECOVER_RATE
        # if rested and not hungry -> SwimState
        if agent.fatigue <= 0:
            agent.fatigue = 0
            agent.is_tired = False
            agent.fsm.change_state(SwimState())

    def leave(self, agent):
        # Deactivate ARRIVE
        agent.steering.stop('ARRIVE')

    def on_msg(self, agent, msg):
        # Willfully ignore all messages
        return True # so will not be passed to global state


class GoHomeState(State):
    """Fatigued and heading home."""

    def enter(self, agent):
        # Activate ARRIVE (home)
        logging.info('Fish: TIRED ({}), going home'.format(agent.fatigue))
        agent.steering.set_target(ARRIVE=agent.home)

    def execute(self, agent):
        # Can we sleep? (based on fatigue and distance home)
        home_dsq = (agent.pos - agent.home).sqnorm()
        if agent.fatigue > GOHOME_URGENCY*home_dsq:
            agent.fsm.change_state(SleepState())

    def leave(self, agent):
        agent.steering.stop('ARRIVE')
        
if __name__ == '__main__':
    pass