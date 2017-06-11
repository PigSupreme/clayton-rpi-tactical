#!/usr/bin/python
"""Logging functions for hydro fish. Still a WIP."""

# for python3 compat
from __future__ import unicode_literals
from __future__ import absolute_import
from __future__ import print_function
from __future__ import division

import sys, pygame
from pygame.locals import QUIT, MOUSEBUTTONDOWN

# TODO: Adjust this depending on where this file ends up.
sys.path.extend(['../vpoints', '../vehicle'])
from point2d import Point2d

# BasePointMass2d defaults
import vehicle2d
import springmass
import hydro_fish

# Math defauls
INF = float('inf')
ZERO_VECTOR = Point2d(0,0)

##############################################################
## Override some of the fish defaults for testing
##############################################################

# This must be called after hydro_fish import to have any effect
vehicle2d.set_physics_defaults(MASS=5.0, MAXSPEED=80.0, MAXFORCE=INF)

# Physics constants
hydro_fish.NODE_RADIUS = 5
hydro_fish.MASS_SCALE = 12
hydro_fish.SIZE_SCALE = 6
hydro_fish.DAMPING_COEFF = 15.0
hydro_fish.HYDRO_FORCE_MULT = 45.0

##############################################################
###### Fish geometry, mass, and spring data
##############################################################
# These are passed to SMHFISH.__init__()

# (Head nodemass, quadheight)
HEAD_DATA = (0.8, 0.45)
# (Length, half-width, nodemass, quad_height) for each segment
BODY_DATA = [(8,4,6.6,2), (12,6,11.0,3), (15,6,8.6,3), (12,4,1.1,2), (10,2,1.1,0.6)]
# (Length, nodemass, quadheight) of tail
TAIL_DATA = (5, 0.4, 8.0)
# Spring constants
SPRING_DATA = {'HEAD': 360,
               'MUSCLE': 80,
               'SOLID': 120,
               'CROSS': 200,
               'TAIL': 140}
##############################################################
### Swimming paramteres (will go into motor control later)
##############################################################

# Muscles are contracted to this proportion of original length
SQUEEZE = 0.88
# Muscle Contraction Frequency (in number of ticks)
FREQ = 140
# Delta_t for physics updates
UPDATE_SPEED = 0.026

##############################################################
# Display-related constants and starting point of fish
##############################################################
SCREEN_SIZE = (1200, 640)
X_OFFSET = 800
Y_OFFSET = 400
HYDRO_FORCE_SCALE = 0.02 # For rendering only
BG_COLOR = (111, 145, 192)
HYDRO_COLOR = (0,90,190)
NODE_COLOR = (0,0,0)

##########################################################
### Additional logging function definitions start here ###
##########################################################
from springmass import DampedMass2d, IdealSpring2d

### Logging for springmass.DampedMass2d
def dm_stats_basic(self):
    """Get basic, static information about this object."""
    results = {'TYPE': 'DAMPEDMASS',
               'MASS': self.mass,
               'DAMPING': self.damping,
               'DYNAMIC_FIELDS': ('Position, Velocity')
               }
    return results

def dm_stats_dynamic(self):
    """Get current non-static information (for logging)."""
    info = (self.pos.ntuple(),
            self.vel.ntuple()
            )
    return info

DampedMass2d.stats_basic = dm_stats_basic
DampedMass2d.stats_dynamic = dm_stats_dynamic

### Logging for springmass.IdealSpring2d
def is_stats_basic(self):
    """Get basic, static information about this object."""
    results = {'TYPE': 'SPRING',
               'LENGTH_NATURAL': self.natlength,
               'SPRING_CONST': self.k,
               'DYNAMIC_FIELDS': ('Current length')
               }
    return results

def is_stats_dynamic(self):
    """Get current non-static information (for logging)."""
    info = (self.curlength,)
    return info

IdealSpring2d.stats_basic = is_stats_basic
IdealSpring2d.stats_dynamic = is_stats_dynamic

from hydro_fish import MuscleSpring2d, HydroQuad2d

### Logging for hydro_fish.MuscleSpring2d
def ms_stats_basic(self):
    """Returns some basic information about this object."""
    results = {'TYPE': 'SPRING_MUSCLE',
               'LENGTH_FLEXED': self.flexlength,
               'LENGTH_CONTRACTED': self.conlength,
               'CONTRACT_FACTOR': self.conlength/self.flexlength,
               'SPRING_CONST': self.k,
               'DYNAMIC_FIELDS': ('Current length',
                                  'Natural length'
                                  )
               }
    return results

def ms_stats_dynamic(self):
    """Get current non-static information (for logging)."""
    info = (self.curlength,
            self.natlength
            )
    return info

MuscleSpring2d.stats_basic = ms_stats_basic
MuscleSpring2d.stats_dynamic = ms_stats_dynamic

### Logging for hydro_fish.HydroQuad2d
def hq_stats_basic(self):
    """Returns some basic information about this object."""

    results = {'TYPE': 'HYDRO_QUAD',
               'BASE_HEIGHT': self.base_h,
               'BASE_MASS': self.base_m.mass,
               'TIP_HEIGHT': self.tip_h,
               'TIP_MASS': self.tip_m.mass,
               'CENTER_T': self.center_t,
               'DYNAMIC_FIELDS': ('Length', 'Area', 'Hydroforce')
               }
    return results

def hq_stats_dynamic(self):
    """Get current non-static information (for logging)."""
    # Compute position and velocity of center of area
    area = self.avg_h * (self.base_m.pos - self.tip_m.pos).norm()
    logged_force = self.current_force
    if logged_force is None:
        logged_force = ZERO_VECTOR
    info = (area, logged_force)
    return info

HydroQuad2d.stats_basic = hq_stats_basic
HydroQuad2d.stats_dynamic = hq_stats_dynamic

### Logging for hydro.fish.SMHFish
from hydro_fish import SMHFish

def fish_print_anatomy(self):
    # Prints initial location of each node
    i = 0
    for node in self.massnodes:
        print('Node %d : Initial position %s' % (i, node.pos.ntuple()))
        i += 1
    # Prints the list of muscles/springs
    i = 0
    print('*** Muscle springs ***')
    for spring in self.springs:
        if i == self.num_muscles:
            print('*** End of muscle springs ***')
        print('Spring %d : Connects nodes %s' % (i, spring.massnodes))
        i += 1
    i = 0
    print('*** Hydro-quads ***')
    for quad in self.hquads:
        print('Quad %d : Between nodes %s' % (i, quad.nodes))
        i += 1 
    print('*** End of anatomy info ***')

SMHFish.print_anatomy = fish_print_anatomy

if __name__ == "__main__":
    pygame.init()

    # Display constants
    DISPLAYSURF = pygame.display.set_mode(SCREEN_SIZE)
    pygame.display.set_caption('Hydro fish logging/plotting')

    fish = SMHFish(HEAD_DATA, BODY_DATA, TAIL_DATA, SPRING_DATA)
    fish.print_anatomy()

    ## Stuff below is for swimming muscle updates ###############
    # This is duplicated from hydro_fish.py for now, but will be
    # replaced once motor controllers are working.
    freq = FREQ
    ticks = 0
    MID_GROUP = 2
    fish.signal_muscles(MID_GROUP, 1) # Midsection, right
    muscles_mid = 1

    ticks2 = freq//2
    # Results seemed better without using the rear swim muscles.
    # To activate them, set REAR_GROUP = 3
    REAR_GROUP = -1
    fish.signal_muscles(REAR_GROUP, 0) # Rear muscles, left
    muscles_rear = 0
    ## End of swimming muscle updates ###########################

    # Additional stuff for plotting
    mid_r_nat = []
    mid_r_act = []
    mid_l_nat = []
    mid_l_act = []
    rearswim_r_act = []
    rearswim_l_act = []
    tailspring_r_act = []
    tailspring_l_act = []
    tailforce_r_x = []
    tailforce_r_y = []
    tailforce_l_x = []
    tailforce_l_y = []    
    xpos = fish.center_pos()[0]
    xspeed = []

    b_running = True
    ############  Main Loop  ######################
    while b_running:
        for event in pygame.event.get():
            if event.type in [QUIT, MOUSEBUTTONDOWN]:
                b_running = False

        ################## Squeeze Test ###########################
        # TODO: Move this into the motor controller class
        if ticks >= freq: # Change direction of midsection
            ticks = 0
            muscles_mid = 1 - muscles_mid
            fish.signal_muscles(MID_GROUP, muscles_mid)

        if ticks2 >= freq: # Change direction of rear swim muscles
            ticks2 = 0
            muscles_rear = 1 - muscles_rear
            fish.signal_muscles(REAR_GROUP, muscles_rear)
        ###########################################################

        # Update fish spring-mass and hydro physics
        fish.update(UPDATE_SPEED)

        ### Additional plot data starts here ###
        # Midection muscles
        muscle_info = fish.muscles[2].stats_dynamic()  # Midsection, right
        mid_r_nat.append(muscle_info[1]) # Natural, right
        mid_r_act.append(muscle_info[0]) # Actual, right
        muscle_info = fish.muscles[3].stats_dynamic()  # Midsection, left
        mid_l_nat.append(muscle_info[1]) # Natural, left
        mid_l_act.append(muscle_info[0]) # Actual, left
        # Rear swim muscles (no signal for now)
        rearswim_r_act.append(fish.muscles[4].stats_dynamic()[0]) # Actual, right
        rearswim_l_act.append(fish.muscles[5].stats_dynamic()[0]) # Actual, left
        # Tail springs
        tailspring_r_act.append(fish.springs[15].stats_dynamic()[0])
        tailspring_l_act.append(fish.springs[16].stats_dynamic()[0])
        # Hydroforces on tail segments
        force_r = fish.hquads[10].stats_dynamic()[1]
        force_l = fish.hquads[11].stats_dynamic()[1]
        tailforce_r_x.append(force_r[0]) # Right force, x-component
        tailforce_l_x.append(force_l[0]) # Left force, x-component
        tailforce_r_y.append(force_r[1]) # Right force, y-component
        tailforce_l_y.append(force_l[1]) # Left force, y-component
        # Velocity of center of position (NOT mass!)
        xposnew = fish.center_pos()[0]
        xspeed.append((xpos - xposnew)/UPDATE_SPEED)
        xpos = xposnew

        # Render
        DISPLAYSURF.fill(BG_COLOR)
        fish.render(DISPLAYSURF)
        pygame.display.flip()
        ticks = ticks + 1

    # Clean-up pygame and plot results
    pygame.quit()

    # Ignore startup jitter and compute average speed
    START_T = 1000
    try:
        xavg = sum(xspeed[START_T:])/len(xspeed[START_T:])
    except ZeroDivisionError:
        xavg = sum(xspeed)/len(xspeed)
    print('Average x velocity of center: %.2f' % xavg)

    import matplotlib.pyplot as plt
    numplots = 6
    plt.subplot(numplots, 1, 1)
    plt.plot(mid_r_nat,'b', mid_r_act,'g',mid_l_act,'r')
    plt.legend(['Signal-R','R','L'])
    plt.ylabel('Midsection')

    plt.subplot(numplots, 1, 2)
    plt.plot(rearswim_r_act,'g',rearswim_l_act,'r')
    plt.legend(['R','L'])
    plt.ylabel('Rear swim')

    plt.subplot(numplots, 1, 3)
    plt.plot(tailspring_r_act,'g',tailspring_l_act,'r')
    plt.legend(['R','L'])
    plt.ylabel('Tail spring')

    plt.subplot(numplots, 1, 4)
    plt.plot(tailforce_r_x,'.g',tailforce_l_x,'.r',ms=1)
    plt.legend(['R','L'])
    plt.ylabel('Tail force\n(x)')

    plt.subplot(numplots, 1, 5)
    plt.plot(tailforce_r_y,'.g',tailforce_l_y,'.r',ms=1)
    plt.legend(['R','L'])
    plt.ylabel('Tail force\n(y)')
    
    plt.subplot(numplots, 1, 6)
    plt.plot(xspeed)
    plt.annotate('Average speed starts here\n %.2f pixels per update' % xavg,
                 (1000,xavg),(1000,xavg/2),arrowprops={'arrowstyle':'->'})
    plt.ylabel('x speed\n of center')

    plt.show()
    #sys.exit()
