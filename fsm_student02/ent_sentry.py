# -*- coding: utf-8 -*-
"""Sentry Entity using simple FSM functionality.
"""

from __future__ import print_function

from random import randint as roll_int

# Game world constants
from fsm_student02.gamedata import WALL_MAX, LADDER_HEIGHT, WINNING_SCORES, GameOver

# Messaging
from fsm_student02.gamedata import LOOK_FOR_SPACE as GO_ATTACK
from fsm_student02.gamedata import LADDER_DOWN as KICKED
from fsm_student02.gamedata import LADDER_PLACED as ATTACKED_AT
from fsm_ex.base_entity import DELAY, SEND_ID, RECV_ID, MSG_TYPE, EXTRA

# Game Entities
from fsm_ex.base_entity import BaseEntity
from fsm_student02.gamedata import CASTLE_WALL, ATTACKER, DEFENDER

# State Machines
from fsm_ex.state_machine import State, StateMachine

class Sentry(BaseEntity):
    """Sentry entity. Comment me!

    """

    # Game behaviour constants
    FATIGUE_LIGHT = 1
    FATIGUE_HEAVY = 20
    FATIGUE_MOVE_COST = 3
    FATIGUE_KNOCKDOWN_COST = 5
    FATIGUE_RECOVERY = 2
    # TODO: There were inconsistencies in the specification for Patrol
    # regarding what distance the ladders could be detected at. These are
    # my best guesses, but the code should be checked.
    SIGHT_PATROL = 4
    SIGHT_REST = 1

    def __init__(self, *args):
        self.wall = args[2]
        args = (args[0], args[1])
        super(Sentry, self).__init__(*args)
        self.name = "Sentry"

        self.location = 0
        self.fatigue = 0

        # Keep track of current direction (for PATROL)
        # This should be either +1 or -1
        self.direction = 1

        # Queue to keep track of what ladders to knock down
        self.task_queue = []
        self.current_task = None

        print("%s : Ready for battle!" % self.name)

        # Set up the FSM for this entity
        self.fsm = StateMachine(self)
        self.fsm.set_state(SentryPatrol(), GlobalSentryState(), None)


    def update(self):
        """Update the sentry's FSM logic."""
        self.fsm.update()

    def receive_msg(self, message):
        # Let the FSM handle any messages
        self.fsm.handle_msg(message)

    def move(self, spaces, direction=None):
        """Move the sentry along the wall.

        The sentry will attempt to move the given number of spaces. If the
        direction is not given, continue in current direction.

        Note: Even though the official requirements say that the sentry can
        move at most one space, this function can handle multiple spaces.
        """
        # If no direction given, use our current one.
        if direction is None:
            direction = self.direction

        new_location = self.location + spaces * direction
        new_location = min(max(0, new_location), WALL_MAX)

        cost = abs(self.location - new_location) * Sentry.FATIGUE_MOVE_COST
        self.location = new_location
        print("%s : Now at space %d." % (self.name, self.location))
        self.change_fatigue(cost)

    def about_face(self):
        """The sentry turns to face the opposite direction."""
        self.direction *= -1
        print("%s : About face! Now facing %d" % (self.name, self.direction))

    def change_fatigue(self, amount):
        self.fatigue += amount
        if self.fatigue < 0:
            self.fatigue = 0

    def get_task_from_queue(self):
        """Finds the first vaild item on the task_queue (which ladder needs
        to be knocked down), and sets the current_task."""
        try:
            space = self.task_queue.pop(0)
            print("%s : There's a ladder at space %d." % (self.name, space))
        except IndexError:
            self.current_task = None
            return

        if self.wall.is_ladder(space):
            self.current_task = space
        else:
            self.current_task = None

    def add_task_to_queue(self, space, check_duplicates=False):
        """Adds a new task to the end of our queue.
        Note: Does not check for duplicate tasks unless explicitly told to.
        """
        if check_duplicates is True:
            if space in self.task_queue:
                return False
        self.task_queue.append(space)
        return True

    def knockdown_ladder(self):
        # In order to check for errors, LADDER_DISPLACED message will be sent
        # by the wall, which then notifies attackers and scores point.
        if self.wall.knockdown_ladder(self.location):
            print("%s : Ladder down, huzzah!" % self.name)
            self.change_fatigue(Sentry.FATIGUE_KNOCKDOWN_COST)
            self.get_task_from_queue()


##################### Start of Sentry states ##################

class GlobalSentryState(State):
    """Global state: document this!
    """

    def execute(self, agent):
        print("%s : Fatigue is now %d." % (agent.name, agent.fatigue))


    def on_msg(self, agent, message):
        if message[MSG_TYPE] == ATTACKED_AT:
            print("%s : ...but I'm at space %d, too far away." % (agent.name, agent.location))
            return True
        else:
            print("%s : A message! Have at ye!" % agent.name)
            return False

##################### End of GlobalSentryState ##################

class SentryPatrol(State):
    """Sentry is patrolling...for somebody to comment this!"""

    def enter(self, agent):
        print("%s : I'm on duty [at space %d]." % (agent.name, agent.location))

    def execute(self, agent):
        # Check for fatigue first
        if agent.fatigue >= Sentry.FATIGUE_HEAVY:
            agent.fsm.change_state(SentryRest())
            return

        # Move in current direction until we reach either end of the wall
        # If ladders can be placed at the end of the walls, this may not work.
        agent.move(1)
        if agent.location == 0 or agent.location == WALL_MAX:
            agent.about_face()

    def leave(self, agent):
        print("%s : I'm off to..." % agent.name)

    def on_msg(self, agent, message):
        if message[MSG_TYPE] == ATTACKED_AT:
            ladder_loc = message[EXTRA]
            print("%s : Ladder was placed at %d..." % (agent.name, ladder_loc))
            if abs(agent.location - ladder_loc) < Sentry.SIGHT_PATROL:
                agent.current_task = ladder_loc
                print("%s : ...going to knock it down!" % agent.name)
                agent.fsm.change_state(SentryDefend())
                return True

            return False

##################### End of SentryPatrol State ##################

class SentryDefend(State):
    """Sentry heads to knock down a ladder."""

    def enter(self, agent):
        print("%s : Defend the castle!" % agent.name)

    def execute(self, agent):
        ladder_loc = agent.current_task

        # If no valid ladder...do what?
        if ladder_loc is None:
            print("%s : Defending, but nothing to do." % agent.name)
            agent.fsm.revert_state()
            return

        # If at ladder, knock it down
        if agent.location == ladder_loc:
            agent.knockdown_ladder()
            agent.fsm.change_state(SentryPatrol())
        # Otherwise, move towards current target
        else:
            if ladder_loc > agent.location:
                agent.direction = 1
                agent.move(1)
            else:
                agent.direction = -1
                agent.move(1)

    def leave(self, agent):
        print("%s : That'll show them!" % agent.name)

##################### End of SentryRepel State ##################

class SentryRest(State):
    """Sentry rest state...document this!"""

    def enter(self, agent):
        print("%s : Taking a break, fatigue is now %d" % (agent.name, agent.fatigue))

    def execute(self, agent):
        print("%s : Resting..." % agent.name)
        agent.change_fatigue(-Sentry.FATIGUE_RECOVERY)
        if agent.fatigue < Sentry.FATIGUE_LIGHT:
            agent.fsm.revert_state()

    def on_msg(self, agent, message):
        if message[MSG_TYPE] == ATTACKED_AT:
            ladder_loc = message[EXTRA]
            print("%s : Ladder was placed at %d..." % (agent.name, ladder_loc))
            if abs(agent.location - ladder_loc) < Sentry.SIGHT_REST:
                print("%s : ...and I'm already there, so knock it down!" % agent.name)
                agent.fsm.change_state(SentryDefend())
                return True
        return False

    def leave(self, agent):
        print("%s: Back to work!" % agent.name)

##################### End of SentryRest State ##################
