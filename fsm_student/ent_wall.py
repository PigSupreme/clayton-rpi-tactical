# -*- coding: utf-8 -*-
"""Wall Entity....Walls are people too?
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
# from fsm_ex.state_machine import State, STATE_NONE, StateMachine


class Wall(BaseEntity):
    """Wall object in a convenient class.

    Note
    ----
    At its inception, this class was not intended to have FSM logic, but does
    need to process messages (using BaseEntity.MessageDispatacher()). Thus we
    use receive_msg() instead of the FSM on_msg().
    """

    # These are used to record the state of each space.
    SPC_BLOCKED, SPC_READY, SPC_LADDER = range(3)

    def __init__(self, *args):
        super(Wall, self).__init__(*args)
        self.name = "Castle Walls"
        # Int
        self.spaces = [Wall.SPC_READY for x in range(WALL_MAX)]
        # Ladders are permitted on odd spaces only
        self.ladders_allowed = [x for x in self.spaces if x % 2 == 1]
        self.scores = {'ATTACKERS': 0, 'DEFENDERS': 0}
        print("%s : Ready for battle!" % self.name)

    def update(self):
        # Clear all blocked spaces (ladders that fell last turn)
        for spc in range(len(self.spaces)):
            if self.spaces[spc] is Wall.SPC_BLOCKED:
                self.spaces[spc] = Wall.SPC_READY

    def receive_msg(self, message):
        # TODO: Write me
        pass

    def is_ladder(self, space):
        """Returns True if space contains a ladder."""
        if self.spaces[space] is Wall.SPC_LADDER:
            return True
        else:
            return False

    def get_nearest_ladder(self, space, dist=WALL_MAX):
        """Location of the nearest ladder, optionally within some distance."""
        spc_range = max(0, space - dist), 1 + min(WALL_MAX, space + dist)
        ladders = filter(lambda x: self.spaces[x] is Wall.SPC_LADDER, spc_range)
        if ladders == ():
            return None
        else:
            return min(ladders, key=lambda x: abs(x - space))
            
    def get_empty_ladder_space(self, space, dist=WALL_MAX):
        """Location of the nearest space that can hold a ladder,
        optionally within some distance."""
        spc_range = max(0, space - dist), 1 + min(WALL_MAX, space + dist)
        empties = filter(lambda x: self.ladders_allowed[x] is Wall.SPC_READY, spc_range)
        if empties == ():
            return None
        else:
            return min(empties, key=lambda x: abs(x - space))
            
    def place_ladder(self, space):
        """Attempt to place a ladder on this wall."""
        if space in self.ladders_allowed and self.spaces[space] is Wall.SPC_READY:
            self.spaces[space] = Wall.SPC_LADDER
            print("%s : Ladder places at space %d." % (self.name, space))
            return True
        else:
            return False

    def knockdown_ladder(self, space):
        """Attempt to knockdown a ladder on this wall."""
        if self.spaces[space] is Wall.SPC_LADDER:
            self.postoffice.post_msg(0,CASTLE_WALL,ATTACKER,LADDER_DOWN,space)
            self.spaces[space] = Wall.SPC_BLOCKED
            self.score_points('DEFENDERS')
            print("%s : Ladder knocked down at space %d." % (self.name, space))
            return True
        else:
            return False

    def score_points(self, team, points=1):
        current = self.scores[team] + points
        self.scores[team] = current
        print("%s : Team %s scored; current score is %d" % (self.name, team, current))
        if current >= WINNING_SCORES[team]:
            raise GameOver(team)
        