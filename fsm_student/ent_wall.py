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
        self.ladders_allowed = [x for x in range(WALL_MAX) if x % 2 == 1]
        self.scores = {'ATTACKERS': 0, 'DEFENDERS': 0}
        print("%s : Ready for battle!" % self.name)

    def update(self):
        # Clear all blocked spaces (ladders that fell last turn)
        for spc in range(len(self.spaces)):
            if self.spaces[spc] is Wall.SPC_BLOCKED:
                self.spaces[spc] = Wall.SPC_READY

    def receive_msg(self, message):
        """Needed for BaseEntity, but not currently used."""
        pass

    def is_ladder(self, space):
        """Returns True if space contains a ladder."""
        if self.spaces[space] == Wall.SPC_LADDER:
            return True
        else:
            return False

    def get_nearest_ladder(self, space=WALL_MAX/2, dist=WALL_MAX):
        """Location of the nearest ladder, optionally within some distance."""
        spc_range = range(max(0, space - dist), min(WALL_MAX, space + dist))
        ladders = filter(lambda x: self.spaces[x] == Wall.SPC_LADDER, spc_range)
        if ladders == []:
            return None
        else:
            return min(ladders, key=lambda x: abs(x - space))

    def get_empty_ladder_space(self): #, space=WALL_MAX/2, dist=WALL_MAX):
        """Location of the nearest space that can hold a ladder,
        optionally within some distance."""
        empties = [x for x in self.ladders_allowed if self.spaces[x] == Wall.SPC_READY]
        print("%s : Empty spaces are %s" % (self.name, str(empties)))
        if empties == []:
            return None
        else:
            return empties[roll_int(0,len(empties)-1)]

    def place_ladder(self, space):
        """Attempt to place a ladder on this wall."""
        if space in self.ladders_allowed and self.spaces[space] == Wall.SPC_READY:
            self.spaces[space] = Wall.SPC_LADDER
            print("%s : Ladder placed at space %d." % (self.name, space))
            ladders = [x for x in range(WALL_MAX) if self.spaces[x] == Wall.SPC_LADDER]
            print("%s : Ladders are now at %s." % (self.name, ladders))
            return True
        else:
            return False

    def knockdown_ladder(self, space):
        """Attempt to knockdown a ladder on this wall."""
        print("%s : Knockdown request at space %d." % (self.name, space))
        if self.spaces[space] is Wall.SPC_LADDER:
            self.postoffice.post_msg(0, CASTLE_WALL, ATTACKER, LADDER_DOWN, space)
            self.spaces[space] = Wall.SPC_BLOCKED
            print("%s : Ladder knocked down at space %d." % (self.name, space))
            self.score_points('DEFENDERS')
            return True
        else:
            return False

    def score_points(self, team, points=1):
        """Score points and check for victory conditions."""
        current = self.scores[team] + points
        self.scores[team] = current
        print("%s : Team %s scored; current score is %d." % (self.name, team, current))
        if current >= WINNING_SCORES[team]:
            raise GameOver(team, self.scores)
