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

class Sentry(BaseEntity):
    """Sentry entity. Comment me!

    """

    # Game behaviour constants
    FATIGUE_LIGHT = 5
    FATIGUE_HEAVY = 20
    FATIGUE_IMMOBILE = 30
    FATIGUE_MOVE_COST = 3
    FATIGUE_KNOCKDOWN_COST = 5
    FATIGUE_RECOVERY = 7
    # TODO: There were inconsistencies in the specification for Patrol
    # regarding what distance the ladders could be detected at. These are
    # my best guesses, but the code should be checked.
    SIGHT_PATROL = 3
    SIGHT_REST = 2

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
        if message[MSG_TYPE] == LADDER_PLACED:
            print("%s : ...but I'm at space %d, too far away." % (agent.name, agent.location))
            return True
        else:
            print("%s : A message! Have at ye!" % agent.name)
            return False

##################### End of GlobalSentryState ##################

class SentryPatrol(State):
    """Sentry is patrolling...for somebody to comment this!"""

    def enter(self, agent):
        print("%s : Now starting patrol from space %d." % (agent.name, agent.location))

    def execute(self, agent):
        # Check for fatigue first
        if agent.fatigue >= Sentry.FATIGUE_HEAVY:
            agent.fsm.change_state(SentryRest())
            return

        ladder = agent.wall.get_nearest_ladder(agent.location, Sentry.SIGHT_PATROL)
        if ladder is not None:
            agent.add_task_to_queue(ladder)
            agent.fsm.change_state(SentryRepel())
            return

        # Otherwise, continue patrol

        # PigSupreme added this to handle end-of-wall locations:
        ########################################################
        if agent.location == 0:
            if agent.direction == 1:
                agent.move(1)
            else:
                agent.about_face()
        if agent.location == WALL_MAX:
            if agent.direction == -1:
                agent.move(1)
            else:
                agent.about_face()
        ########################################################

        # We do something different if within 1 space of end of wall:
        # PigSupreme cleaned this up to work with end-of-wall code above.
        # TODO: Consider fixing this, sentries seem to linger too long.
        if agent.location == 1:
            d4 = roll_int(1, 4)
            if d4 > 1 and agent.direction == -1:
                agent.about_face()
        elif agent.location == WALL_MAX - 1:
            d4 = roll_int(1, 4)
            if d4 > 1 and agent.direction == 1:
                agent.about_face()
        else:
            d5 = roll_int(1, 5)
            if d5 == 2:
                agent.about_face()
            elif d5 > 2:
                agent.move(1)

    def on_msg(self, agent, message):
        """Note: Since it wasn't specified, I decided to have this return
        False if the ladder was not within SIGHT_PATROL, so that it might
        be handled by a global state."""
        if message[MSG_TYPE] == LADDER_PLACED:
            ladder_loc = message[EXTRA]
            print("%s : Ladder was placed at %d..." % (agent.name, ladder_loc))
            if abs(agent.location - ladder_loc) < Sentry.SIGHT_PATROL:
                agent.add_task_to_queue(ladder_loc)
                print("%s : ...going to repel it. Task queue is %s." % (agent.name, str(agent.task_queue)))
                agent.fsm.change_state(SentryRepel())
                return True
        return False

##################### End of SentryPatrol State ##################

class SentryRepel(State):
    """The specs on this state don't check for immobilization..."""

    def enter(self, agent):
        # TODO: Spec says "Identify location of ladder." Which one?
        # Assuming the first ladder on this sentry's task_queue.
        agent.get_task_from_queue()
        if agent.current_task and agent.wall.is_ladder(agent.current_task):
            print("%s : Repelling ladder at space %d, I'm at space %d." % (agent.name, agent.current_task, agent.location))
        else:
            # Ladder is gone...we must have reverted from resting, or somebody
            # else took care of it
            print("%s : No ladders to repel...")

    def execute(self, agent):
        ladder_loc = agent.current_task

        # If no valid ladder...do what?
        if ladder_loc is None:
            print("%s : Orders from PigSupreme!" % agent.name)
            agent.fsm.revert_state()
            return

        # If at ladder, knock it down
        if agent.location == ladder_loc:
            agent.knockdown_ladder()
        # Otherwise, move towards current target
        else:
            if ladder_loc > agent.location:
                agent.direction = 1
                agent.move(1)
            else:
                agent.direction = -1
                agent.move(1)

    def on_msg(self, agent, message):
        if message[MSG_TYPE] == LADDER_PLACED:
            ladder_loc = message[EXTRA]
            print("%s : Ladder was placed at %d..." % (agent.name, ladder_loc))
            if abs(agent.location - ladder_loc) < Sentry.SIGHT_PATROL:
                agent.add_task_to_queue(ladder_loc)
                print("%s : ...and I'll get there. Task queue is %s." % (agent.name, str(agent.task_queue)))
                return True
        return False

##################### End of SentryRepel State ##################

class SentryRest(State):
    """Sentry rest state...document this!"""

    def enter(self, agent):
        print("%s : Taking a break, fatigue is now %d" % (agent.name, agent.fatigue))

    def execute(self, agent):
        print("%s : Resting..." % agent.name)
        agent.change_fatigue(-Sentry.FATIGUE_RECOVERY)
        # Since it was not specified how to come out of being immobilized,
        # I instead put an immobilization check into on_msg. If there is
        # other immobilized-specific behaviour, make a new state for it.
        if agent.fatigue < Sentry.FATIGUE_LIGHT:
            agent.fsm.change_state(SentryPatrol())

    def on_msg(self, agent, message):
        """Note: Moved the immobilization check into this function.
        Also, since it wasn't specified, I decided to have this return
        False if the ladder was not within SIGHT_REST, so that it might
        be handled by a global state."""
        # If immobilized, do nothing
        if agent.fatigue > Sentry.FATIGUE_IMMOBILE:
            return False

        if message[MSG_TYPE] == LADDER_PLACED:
            ladder_loc = message[EXTRA]
            if abs(agent.location - ladder_loc) < Sentry.SIGHT_REST:
                agent.fsm.change_state(SentryRepel())
                return True
        return False

    def leave(self, agent):
        print("%s: Returning to duty!" % agent.name)

##################### End of SentryRest State ##################
