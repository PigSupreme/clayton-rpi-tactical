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
import matplotlib.pyplot as plt

# Math defauls
INF = float('inf')
ZERO_VECTOR = Point2d(0,0)

##############################################################
## Override some of the fish defaults for testing
## Duck punching...you'll be good at it!
##############################################################

# This must be called after hydro_fish import to have any effect
vehicle2d.set_physics_defaults(MAXSPEED=80.0, MAXFORCE=INF)

# Physics constants
hydro_fish.NODE_RADIUS = 5
hydro_fish.MASS_SCALE = 12
hydro_fish.SIZE_SCALE = 6
hydro_fish.DAMPING_COEFF = 15.0
hydro_fish.HYDRO_FORCE_MULT = 8.0

##############################################################
###### Fish geometry, mass, and spring data
##############################################################
# These are passed to SMHFISH.__init__()

# (Head nodemass, quadheight)
HEAD_DATA = (0.8, 0.45)
# (Length, half-width, nodemass, quad_height) for each segment
BODY_DATA = [(8,4,6.6,8), (12,6,11.0,12), (15,6,8.6,12), (12,4,1.1,8), (10,2,1.1,2)]
# (Length, nodemass, quadheight) of tail
TAIL_DATA = (5, 0.4, 8.0)
# Spring constants
SPRING_DATA = {'HEAD': 360,
               'MUSCLE': 90,
               'SOLID': 140,
               'CROSS': 220,
               'TAIL': 140}

##############################################################
### Swimming parameters (will go into motor control later)
##############################################################

# Muscles are contracted to this proportion of original length
SQUEEZE = 0.88
# Muscle Contraction Frequency (in number of ticks)
FREQ = 140
# Delta_t for physics updates
UPDATE_SPEED = 0.0235

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

####################################################################
### Logging for springmass.IdealSpring2d
####################################################################
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

####################################################################
### Logging for hydro_fish.MuscleSpring2d
####################################################################
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

####################################################################
### Logging for hydro_fish.HydroQuad2d
####################################################################
def hq_stats_basic(self):
    """Returns some basic information about this object."""

    results = {'TYPE': 'HYDRO_QUAD',
               'BASE_HEIGHT': self.base_h,
               'BASE_MASS': self.base_m.mass,
               'TIP_HEIGHT': self.tip_h,
               'TIP_MASS': self.tip_m.mass,
               'CENTER_T': self.center_t,
               'DYNAMIC_FIELDS': ('Area', 'Hydroforce', 'Area Center')
               }
    return results

def hq_stats_dynamic(self):
    """Get current non-static information (for logging)."""
    area = self.avg_h * (self.base_m.pos - self.tip_m.pos).norm()
    logged_force = self.current_force
    if logged_force is None:
        logged_force = ZERO_VECTOR
     
    info = (area, logged_force, self.pos, self.vel)
    return info

HydroQuad2d.stats_basic = hq_stats_basic
HydroQuad2d.stats_dynamic = hq_stats_dynamic

####################################################################
### Logging for hydro.fish.SMHFish
####################################################################
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

####################################################################
### Additional Logging/Plotting functions not attached to hydro_fish
####################################################################
def plot_fishdata_shape(head, body, tail):
    """Plots the overhead and side geometry for the given fish data."""
    x, y, z = (0, 0, head[1]/2.0)
    overhead_R = [(x,y,z)]
    for p in body:
        x = x + p[0]
        y = p[1]
        z = p[3]/2.0
        overhead_R.append((x,y,z))
    overhead_R.append((x+ tail[0], 0, tail[2]))
    x_list = [x for (x,y,z) in overhead_R]
    y_list_R = [y for (x,y,z) in overhead_R]
    y_list_L = [-y for y in y_list_R]
    h_list = [z for (x,y,z) in overhead_R]

    # This adds some space between overhead and side views
    # Tried this with subplots, but they were being unruly
    ZBASE = -(5 + max(y_list_R) + max(h_list))
    h_list_top = [ZBASE + z for z in h_list]
    h_list_bot = [ZBASE - z for z in h_list]

    # Overhead geometry
    plt.fill_between(x_list, y_list_R, y_list_L)
#    plt.plot(x_list, y_list_R, 'b')
#    plt.plot(x_list, y_list_L, 'b')
    # Side view
    plt.fill_between(x_list, h_list_top, h_list_bot)
#    plt.plot(x_list, h_list_top, 'k')
#    plt.plot(x_list, h_list_bot, 'k')
    plt.xticks(x_list,range(len(x_list)))
    plt.yticks((0,ZBASE),('Top','Side'))
    plt.grid(True)
    plt.title('Initial fish geometry')
    plt.axes().set_aspect('equal', 'box')
    plt.show()

if __name__ == "__main__":
    # Show the fish shape
    plot_fishdata_shape(HEAD_DATA, BODY_DATA, TAIL_DATA)

    pygame.init()

    # Display constants
    DISPLAYSURF = pygame.display.set_mode(SCREEN_SIZE)
    pygame.display.set_caption('Hydro fish logging/plotting')

    fish = SMHFish(HEAD_DATA, BODY_DATA, TAIL_DATA, SPRING_DATA)
    #fish.print_anatomy()

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

    #############################################################
    # Placeholders for data to be plotted
    #############################################################
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
    tailpos_y = []
    xpos = fish.center_pos()[0]
    xspeed = []
    
    tailquad_r_yvel = []
    tailquad_l_yvel = []

    b_running = True
    ###########################################################
    ############  Main Loop Start
    ###########################################################
    while b_running:
        for event in pygame.event.get():
            if event.type in [QUIT, MOUSEBUTTONDOWN]:
                b_running = False

        ################## Squeeze Test ###########################
        # TODO: This is duplicated from hydro_fish.py; will need to
        # ...update once motor controller code is working
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

        ###########################################################
        ### Plot data update starts here 
        ###########################################################
        # Midsection muscles
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
        # Tail hydroquads
        tailinfo_r = fish.hquads[10].stats_dynamic()
        tailinfo_l = fish.hquads[11].stats_dynamic()
        force_r = tailinfo_r[1] # Hydroforce on right side
        force_l = tailinfo_l[1] # Hydroforce on left side
        tailforce_r_x.append(force_r[0]) # Right force, x-component
        tailforce_l_x.append(force_l[0]) # Left force, x-component
        tailforce_r_y.append(force_r[1]) # Right force, y-component
        tailforce_l_y.append(force_l[1]) # Left force, y-component
        # y-velocities of center of area of tail quads
        tailquad_r_yvel.append(tailinfo_r[3][1])
        tailquad_l_yvel.append(tailinfo_l[3][1])
        # y-velocity of tail node
        tailpos_y.append(fish.massnodes[1].stats_dynamic()[0][1])
        # Velocity of center of position (NOT mass!)
        # Note: This ignores head/tail nodes; too much judder
        xposnew = fish.center_pos()[0]
        xspeed.append((xpos - xposnew)/UPDATE_SPEED)
        xpos = xposnew
        ###########################################################

        # Render
        DISPLAYSURF.fill(BG_COLOR)
        fish.render(DISPLAYSURF)
        pygame.display.flip()
        ticks = ticks + 1

    ###########################################################
    ############  End of Main Loop
    ###########################################################

    # Clean-up pygame and plot results
    pygame.quit()

    # Ignore startup jitter and compute average speed
    START_T = 1000
    try:
        xavg = sum(xspeed[START_T:])/len(xspeed[START_T:])
    except ZeroDivisionError:
        xavg = sum(xspeed)/len(xspeed)
    print('Average x velocity of center: %.2f' % xavg)

    numplots = 8
    sbase = plt.subplot(numplots, 1, 1)
    plt.plot(mid_r_nat,'b', mid_r_act,'g',mid_l_act,'r')
    plt.legend(['Signal-R','R','L'])
    plt.ylabel('Midsection')

    plt.subplot(numplots, 1, 2, sharex=sbase)
    plt.plot(rearswim_r_act,'g',rearswim_l_act,'r')
    plt.legend(['R','L'])
    plt.ylabel('Rear swim')

    plt.subplot(numplots, 1, 3, sharex=sbase)
    plt.plot(tailspring_r_act,'g',tailspring_l_act,'r')
    plt.legend(['R','L'])
    plt.ylabel('Tail spring')

    plt.subplot(numplots, 1, 4, sharex=sbase)
    plt.plot(tailforce_r_x,'.g',tailforce_l_x,'.r',ms=1)
    plt.legend(['R','L'])
    plt.ylabel('Tail force (x)')

    plt.subplot(numplots, 1, 5, sharex=sbase)
    plt.plot(tailforce_r_y,'.g',tailforce_l_y,'.r',ms=1)
    plt.legend(['R','L'])
    plt.ylabel('Tail force (y)')

    plt.subplot(numplots, 1, 6, sharex=sbase)
    plt.plot(tailquad_r_yvel,'.g',tailquad_l_yvel,'.r',ms=1)
    plt.legend(['R','L'])
    plt.ylabel('Tail quad\nvelocity (y)')
    
    plt.subplot(numplots, 1, 7, sharex=sbase)
    plt.plot(tailpos_y, '.k',ms=1)
    plt.ylabel('Tail node\n(y)')
    
    plt.subplot(numplots, 1, 8, sharex=sbase)
    plt.plot(xspeed)
    plt.annotate('Average speed starts here\n %.2f pixels per update' % xavg,
                 (1000,xavg),(1000,xavg/2),arrowprops={'arrowstyle':'->'})
    plt.ylabel('x speed\n of center')

    plt.show()
    #sys.exit()
