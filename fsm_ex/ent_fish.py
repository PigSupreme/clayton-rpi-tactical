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
from vpoints.point2d import Point2d

FATIGUE_THRESHOLD = 5000
FATIGUE_RECOVER_RATE = 5
SLEEP_DECEL = 10
FISH_HESITANCE = 5.0

HUNGER_THRESHOLD = 1200
EAT_RADIUS_SQ = 20**2
HUNTING_UPDATE_RATE = 50

# Used to set maxspeed based on hunger/fatigue, see the function below
FISH_SPEED_MAX = 15
FISH_SPEED_MIN = 5
FISH_SPEED_MULT = 150
FISH_SPEED_HSCALE = 1
FISH_SPEED_FSCALE = 2
def compute_maxspeed(h, f):
    """Current maximum speed based on hunger/fatigue.
    
    If m h, f is current maxspeed, hunger, fatigue, then
    m = MIN + MULT*(MAX-MIN)/(MULT + HSCALE*h + FSCALE*f)
    """
    return FISH_SPEED_MIN + FISH_SPEED_MULT*(FISH_SPEED_MAX-FISH_SPEED_MIN)//(FISH_SPEED_MULT + FISH_SPEED_HSCALE*h + FISH_SPEED_FSCALE*f)

# Higher values will prioritize going home over sleeping
GOHOME_URGENCY = 100

# Distance thresholds for TAKECOVER
# If shark is closer than this, we EVADE instead
EVADE_SMALL = 120
EVADE_SMALL_SQR = EVADE_SMALL**2
EVADE_MEDIUM_SQR = 150**2

# Respawn after this many updates
RESPAWN_RATE = 600

class Plus8Fish(SimpleVehicle2d):
    """Fish-type vehicle with simple FSM logic."""

    def __init__(self, ent_id, radius, home_pos, start_vel, sprite_data, feeder=None):
        SimpleVehicle2d.__init__(self, home_pos, radius, start_vel, sprite_data)
        self.ent_id = ent_id
        self.home = home_pos
        self.fatigue = 0
        self.hunger = 0

        # FSM setup
        fsm = StateMachine(self)
        fsm.set_state(InitialFishState(), GlobalFishState())
        self.fsm = fsm
        self.feeder = feeder

    def flocking_on(self):        
        for behaviour in ('SEPARATE', 'ALIGN', 'COHESION'):
            self.steering.resume(behaviour)

    def flocking_off(self):        
        for behaviour in ('SEPARATE', 'ALIGN', 'COHESION'):
            self.steering.pause(behaviour)       


##########################################
### State logic definitions start here ###
##########################################

class InitialFishState(State):
    """Dummy initial state for first update cycle, also used after respawn."""

    def execute(self, agent):
        agent.hunger = 0
        agent.fatigue = 0
        agent.alive = True
        agent.steering.set_target(AVOID=agent.obs, WALLAVOID=[35, agent.walls])
        agent.steering.resume('AVOID')
        agent.steering.resume('WALLAVOID')
        # This sets up behaviours for easy use later
        agent.steering.set_target(EVADE=agent.shark)
        agent.steering.pause('EVADE')
        agent.steering.set_target(TAKECOVER=(agent.shark, agent.obs, EVADE_SMALL))
        agent.steering.pause('TAKECOVER')
        
        agent.fsm.change_state(SwimState())

class GlobalFishState(State):
    # No enter method here; use initial state instead

    def execute(self, agent):
        # Steering/Physics update
        agent.move(agent.UPDATE_SPEED)
        agent.maxspeed = compute_maxspeed(agent.hunger, agent.fatigue)

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
        if msg == 'UR_EATEN':
            logging.info('Fish {}: Was eaten by shark'.format(agent.ent_id))
            agent.fsm.change_state(DeadState())
            return True
        if msg == 'SHARK':
            agent.fsm.change_state(EvadeState())
            return True
        if msg == 'TIRED' and agent.fatigue > FATIGUE_THRESHOLD:
            agent.fsm.change_state(GoHomeState())
            return True
        if msg == 'HUNGRY' and agent.hunger > HUNGER_THRESHOLD:
            agent.fsm.change_state(HuntState())
            return True
        return False


class SwimState(State):
    """Default state; just flock with other fish."""

    def enter(self, agent):
        # Activate WANDER
        agent.steering.set_target(WANDER=(90, 15, 3))
        agent.flocking_on()
        logging.info('Fish {}: Fatigue = {}, Hunger = {}'.format(agent.ent_id, agent.fatigue, agent.hunger))

    def leave(self, agent):
        # Stop WANDER
        agent.steering.stop('WANDER')
        agent.flocking_off()


class EatState(State):
    """Gateway state for consuming food."""

    def enter(self, agent):
        pass

    def execute(self, agent):
        # Food was eaten before transition, just reset hunger
        agent.hunger = 0
        agent.fsm.change_state(SwimState())

    def on_msg(self, agent, msg):
        # Willfully ignore all messages except for SHARK and UR_EATEN
        if msg == 'SHARK' or msg == 'UR_EATEN':
            return False # and thus pass up to global state
        return True


class HuntState(State):
    """Find food and go to it."""

    def enter(self, agent):
        # TODO: Check if we need this here
        agent.flocking_on()
        
        # Get closest food source. If not found, we'll stay in this state
        # and try again later.
        agent.food_pos = agent.feeder.nearest_food_pos(agent.pos)
        if agent.food_pos is not None:
            logging.info('Fish {}: HUNGRY ({}), Hunting food at ({:.0f}, {:.0f})'.format(agent.ent_id, agent.hunger, *agent.food_pos.ntuple()[:]))
            agent.steering.set_target(ARRIVE=agent.food_pos)
        # Check our current target every so often
        agent.hunting_countdown = HUNTING_UPDATE_RATE

    def execute(self, agent):
        # Try eating any nearby food, regardless of our current target
        if agent.feeder.chomp(agent):
            agent.fsm.change_state(EatState())
        else:
            agent.hunting_countdown -= 1
            if agent.hunting_countdown <= 0:
                self.enter(agent)
                
    def leave(self, agent):
        # stop SEEK (to food)
        agent.food_pos = None
        agent.steering.stop('ARRIVE')
        agent.flocking_off()

#    def on_msg(self, agent, msg):
#        # FOOD_NEAR -> EatState
#        return False


class EvadeState(State):
    """Get away from the shark."""

    def enter(self, agent):
        # TODO: stop all but AVOID
        agent.steering.resume('TAKECOVER')
        # if shark is close
        #   activate EVADE
        #   activate TAKE_COVER

    def execute(self, agent):
        dsq = (agent.pos - agent.shark.pos).sqnorm()
        if dsq < EVADE_SMALL_SQR:
            agent.steering.pause('TAKECOVER')
            agent.steering.resume('EVADE')
        elif dsq < EVADE_MEDIUM_SQR:
            agent.steering.pause('EVADE')
            agent.steering.resume('TAKECOVER')
        else:
            agent.fsm.change_state(SwimState())

    def leave(self, agent):
        agent.steering.pause('EVADE')
        agent.steering.pause('TAKECOVER')

    def on_msg(self, agent, msg):
        if msg != 'UR_EATEN':
            return True
        return False


class SleepState(State):
    """Sleeping until fully rested."""

    def enter(self, agent):
        # Deactivate all steering??
        agent.flocking_off()
        # Activate BRAKE
        agent.steering.set_target(BRAKE=0.5)
        #target = agent.pos + agent.vel.scm(SLEEP_DECEL)

    def execute(self, agent):
        # Gradually reduce fatigue
        agent.fatigue -= FATIGUE_RECOVER_RATE
        # if rested and not hungry -> SwimState
        if agent.fatigue <= 0:
            agent.fatigue = 0
            agent.is_tired = False
            agent.fsm.change_state(SwimState())

    def leave(self, agent):
        agent.steering.stop('BRAKE')
        agent.flocking_on()

    def on_msg(self, agent, msg):
        # Willfully ignore all messages except eaten
        if msg != 'UR_EATEN':
            return True # so will not be passed to global state
        return False


class GoHomeState(State):
    """Fatigued and heading home."""

    def enter(self, agent):
        # Activate ARRIVE (home)
        logging.info('Fish {}: TIRED ({}), going home'.format(agent.ent_id, agent.fatigue))
        agent.steering.set_target(ARRIVE=agent.home)

    def execute(self, agent):
        # Can we sleep? (based on fatigue and distance home)
        home_dsq = (agent.pos - agent.home).sqnorm()
        if agent.fatigue > GOHOME_URGENCY*home_dsq:
            agent.fsm.change_state(SleepState())

    def leave(self, agent):
        agent.steering.stop('ARRIVE')


class DeadState(State):
    """Fish was eaten; move sprite away and respawn later."""
    
    def enter(self, agent):
        # Pause all steering behaviours
        for behaviour in list(agent.steering.targets.keys()):
            agent.steering.pause(behaviour)
        agent.pos = Point2d(-9000,-9000)
        agent.vel = Point2d(0,0)
        agent.alive = False
        agent.until_respawn = RESPAWN_RATE
        
    def execute(self, agent):
        agent.until_respawn -= 1
        if agent.until_respawn <= 0:
            agent.fsm.change_state(InitialFishState())
            
    def leave(self, agent):
        logging.info('Fish {}: now respawning at {}'.format(agent.ent_id, agent.home))
        agent.pos = agent.home
        agent.hunger = 0
        agent.fatigue = 0
        agent.vel = Point2d(0,0)
        agent.steering.resume('AVOID')
        agent.steering.resume('WALLAVOID')
            
    def on_msg(self, agent, msg):
        """Ignore all messages when dead."""
        return True
    

if __name__ == '__main__':
    pass