#!/usr/bin/env python
"""Fish Entity using simple FSM functionality.
"""

# for python3 compat
from __future__ import unicode_literals
from __future__ import absolute_import
from __future__ import print_function

import logging, sys

#from fsm_ex.base_entity import BaseEntity
from fsm_ex.state_machine import State, STATE_NONE, StateMachine

# Note: Adjust this depending on where this file ends up.
sys.path.append('..')
from vehicle.vehicle2d import SimpleVehicle2d

INF = float('inf')

# Not used
FATIGUE_THRESHOLD = 5000
FATIGUE_RECOVER_RATE = 5
SLEEP_DECEL = 10

EAT_RADIUS_SQ = 35**2
HUNGER_PER_FISH = 400
HUNGER_THRESHOLD = 4*HUNGER_PER_FISH
HUNTING_RANGE_SQ = 300**2
HUNTING_UPDATE_RATE = 200

SHARK_SPEED_BOOST = 0.45

# Higher values will prioritize going home over sleeping
#GOHOME_URGENCY = 100

class Plus8Shark(SimpleVehicle2d):
    """Shark-type vehicle with simple FSM logic."""

    def __init__(self, ent_id, radius, home_pos, start_vel, sprite_data, feeder=None):
        SimpleVehicle2d.__init__(self, home_pos, radius, start_vel, sprite_data)
        self.ent_id = ent_id
        self.home = home_pos
        self.fatigue = 0
        self.hunger = 0

        # FSM setup
        fsm = StateMachine(self)
        fsm.set_state(InitialSharkState(), GlobalSharkState())
        self.fsm = fsm
        self.feeder = feeder


##########################################
### State logic definitions start here ###
##########################################

class InitialSharkState(State):
    """Dummy initial state for first update cycle."""

    def execute(self, agent):
        agent.hunger = 0
        agent.fatigue = 0
        agent.steering.set_target(AVOID=agent.obs, WALLAVOID=[50, agent.walls])
        agent.fsm.change_state(SwimState())

class GlobalSharkState(State):
    # No enter method here; use initial state instead

    def execute(self, agent):
        # Steering/Physics update
        agent.move(agent.UPDATE_SPEED)

        # TODO: Update agent.maxspeed based on hunger/fatigue

        agent.fatigue += 1
        agent.hunger += 1
        # Fatigue check (make this periodic rather than each update??)
        if False: #agent.fatigue > FATIGUE_THRESHOLD:
            pass
            #agent.fsm.handle_msg('TIRED')
        else:
            # Hunger has lower priority than sleep
            if agent.hunger > HUNGER_THRESHOLD:
                agent.fsm.handle_msg('HUNGRY')

    def on_msg(self, agent, msg):
#        if msg == 'TIRED' and agent.fatigue > FATIGUE_THRESHOLD:
#            agent.fsm.change_state(GoHomeState())
#            return True
        if msg == 'HUNGRY' and agent.hunger > HUNGER_THRESHOLD:
            agent.fsm.change_state(HuntState())
            return True
        # Otherise message was ignored
        return False


class SwimState(State):
    """Default state."""

    def enter(self, agent):
        # Activate WANDER
        agent.steering.set_target(WANDER=(90, 40, 3))
        logging.debug('Shark: Fatigue = %d, Hunger = %d' % (agent.fatigue, agent.hunger))

    def execute(self, agent):
        # TODO: Flocking here
        pass

    def leave(self, agent):
        # Stop WANDER
        agent.steering.stop('WANDER')


class EatState(State):
    """Gateway state for consuming food."""

    def enter(self, agent):
        # TODO: Send message that food is being eaten
        logging.info('Shark: Eating fish! Hunger now {}'.format(agent.hunger))
        agent.target_prey.fsm.handle_msg('UR_EATEN')

    def execute(self, agent):
        # Food was eaten before transition, just reset hunger
        agent.hunger -= HUNGER_PER_FISH
        agent.target_prey = None
        if agent.hunger > HUNGER_THRESHOLD:
            agent.fsm.change_state(HuntState())
        else:
            agent.fsm.change_state(SwimState())

    def on_msg(self, agent, msg):
        # Willfully ignore all messages
        return True
    

class HuntState(State):
    """Find food and chase after it."""

    def enter(self, agent):
        agent.maxspeed += SHARK_SPEED_BOOST
        # TODO: This assumes shark keeps track of the fish
        # TODO: Have global state manage the prey list??
        # For now, find the location of the nearest prey
        target = None
        dsq = HUNTING_RANGE_SQ
        for fish in agent.prey:
           #fish_loc = Point2d(*food.rect.center)
           food_dsq = (agent.pos - fish.pos).sqnorm()
           if food_dsq < dsq:
               target = fish
               dsq = food_dsq
        
        agent.target_prey = target
        if target is not None:
            logging.info('Shark: HUNGRY ({}), Hunting prey at ({:.0f}, {:.0f})'.format(agent.hunger, *target.pos.ntuple()[:]))
            agent.steering.set_target(PURSUE=target)
            target.fsm.handle_msg('SHARK')
        else:
            logging.debug('Shark: HUNGRY ({}), but no prey found'.format(agent.hunger))
        agent.hunting_countdown = HUNTING_UPDATE_RATE

    def execute(self, agent):
        # Update our target every so often...
        # ...cheating on this by re-calling enter
        # ...so we need to adjust the boost
 
        agent.hunting_countdown -= 1
        if agent.hunting_countdown <= 0:
            agent.maxspeed -= SHARK_SPEED_BOOST
            self.enter(agent)
            
        # TODO: Check current food target
        if agent.target_prey is None:
            agent.fsm.change_state(SwimState())
        else:
            if (agent.pos - agent.target_prey.pos).sqnorm() < EAT_RADIUS_SQ:
                # Eat fish
                agent.fsm.change_state(EatState())

    def leave(self, agent):
        # Stop PURSUE
        agent.maxspeed -= SHARK_SPEED_BOOST
        agent.steering.stop('PURSUE')

    def on_msg(self, agent, msg):
        # FOOD_NEAR -> EatState
        pass


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


#class GoHomeState(State):
#    """Fatigued and heading home."""
#
#    def enter(self, agent):
#        # Activate ARRIVE (home)
#        logging.info('Fish: TIRED ({}), going home'.format(agent.fatigue))
#        agent.steering.set_target(ARRIVE=agent.home)
#
#    def execute(self, agent):
#        # Can we sleep? (based on fatigue and distance home)
#        home_dsq = (agent.pos - agent.home).sqnorm()
#        if agent.fatigue > GOHOME_URGENCY*home_dsq:
#            agent.fsm.change_state(SleepState())
#
#    def leave(self, agent):
#        agent.steering.stop('ARRIVE')

if __name__ == '__main__':
    pass