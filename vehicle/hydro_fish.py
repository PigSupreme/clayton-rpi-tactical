#!/usr/bin/python
"""Springmass fish with hydro forces. Still a WIP."""

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
# Additional spring-mass classes
from springmass import DampedMass2d, IdealSpring2d

# Math defauls
from math import sqrt
INF = float('inf')

# This must be called after springmass imports to have any effect
vehicle2d.set_physics_defaults(MASS=5.0, MAXSPEED=80.0, MAXFORCE=50000.0)

# Physics constants
NODE_RADIUS = 5
MASS_SCALE = 12
SIZE_SCALE = 6
DAMPING_COEFF = 15.0
HYDRO_FORCE_MULT = 45.0

###### Fish geometry, mass, and spring data ##################
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

# Muscles are contracted to this proportion of original length
SQUEEZE = 0.88
# Muscle Contraction Frequency (in number of ticks)
FREQ = 140

# Display-related constants and starting point of fish
SCREEN_SIZE = (1200, 640)
X_OFFSET = 800
Y_OFFSET = 400
HYDRO_FORCE_SCALE = 0.02 # For rendering only
HYDRO_COLOR = (0,90,190)
NODE_COLOR = (0,0,0)

UPDATE_SPEED = 0.026

class MuscleSpring2d(IdealSpring2d):
    """A spring with the ability to contract and flex. See Notes.

    Parameters
    ----------
    spring_constant: positive float
        Linear Spring Constant (Hooke's Law).
    mass1: BasePointMass2d
        Point mass at the base of this spring.
    mass2: BasePointMass2d
        Point mass at the end of this spring.
    contraction_factor: positive float
        Proportion of original length to which this muscle can be contracted.

    Notes
    -----

    This inherits from IdealSpring2d, so the order of masses is not important.
    The length between masses is automatically computed on initialization, and
    the muscle is treated at completely flexed/loose. Contraction is acheived
    mathematically by changing the natural length of the underlying spring; see
    the contract() method for further details.
    """
    def __init__(self, spring_constant, mass1, mass2, contraction_factor):
        IdealSpring2d.__init__(self, spring_constant, mass1, mass2)
        self.flexlength = self.natlength
        self.conlength = contraction_factor * self.natlength
        # For later convenience
        self.conslope = self.flexlength - self.conlength
        self.contracted = 0

    def contract(self, squeeze_factor):
        """Contract this muscle by altering its effective rest length.

        Parameters
        ----------
        squeeze_factor: float
            Value from 0 (no contraction) to 1 (fully contracted)
        """
        # Change the natural/rest length of the underlying IdealSpring2d
        self.natlength = self.flexlength - squeeze_factor * self.conslope
        self.contracted = squeeze_factor


class MuscleControl(object):
    """TODO: Helper class for controlling muscle movements over time."""
    def __init__(self):
        raise NotImplementedError


class HydroQuad2d(object):
    """Two-dimension segment representing a quad under fluidic force.

    Parameters
    ----------

    base_mass: BasePointMass2d
        Point mass at the 2D coordinates of the quad base.
    base_height: non-negative float
        Height of the quad at the base coordinates.
    tip_mass: BasePointMass2d
        Point mass at the 2D coordinates of the quad tip.
    tip_height: non-negative float
        Height of the quad at the tip coordinates.

    Notes
    -----

    This models a 2D trapezoid seen from directly above as a line segment. For
    our spring-mass fish, this segment connects two nodes, so each HydroQuad2d
    overlaps one of the fish springs. I'm seperating this class from the springs
    for future flexibility; our quads here may become 3D polys later.

    The fish should be on the left of vector from base to tip.
    """
    def __init__(self, base_mass, base_height, tip_mass, tip_height):
        self.base_m = base_mass
        self.base_h = base_height
        self.tip_m = tip_mass
        self.tip_h = tip_height
        # Shortcut used in area computations of a trapezoid
        self.avg_h = (base_height + tip_height)/2

        # Location of center of mass as a proportion of total segment length;
        # used in standard parametric equations.
        if base_height == tip_height:
            # Rectangles don't work in the formula below.
            self.center_t = 0.5
        else:
            # Otherwise, use center of AREA of a trapezoid.
            numer = sqrt(2*(tip_height**2 + base_height**2)) - 2*base_height
            self.center_t = numer/(2*(tip_height - base_height))

    def exert_fluid_force(self, delta_t=1.0):
        """Compute and apply force to end masses based on surface velocity.

        TODO: Check/explain the fluid dynamics being used here.
        """
        # Compute position and velocity of center of area
        ct = self.center_t  # For convenience in formulas belotw
        self.pos = self.base_m.pos.scm(1-ct) + self.tip_m.pos.scm(ct)
        self.vel = self.base_m.vel.scm(1-ct) + self.tip_m.vel.scm(ct)

        # Compute total fluidic force
        contour_vec = self.tip_m.pos - self.base_m.pos
        normal_in = contour_vec.left_normal()
        dotp = self.vel * normal_in

        # Only apply force if center is moving in an outward direction from body
        if dotp < 0:
            # Fluid volume displaced by this quad during last update step
            volume = delta_t*self.avg_h*contour_vec.norm()
            # Force is proportional (somehow...) to volume of displaced fluid
            total_force = normal_in.scm(-dotp*volume*HYDRO_FORCE_MULT/normal_in.sqnorm())
            # Apply to masses at base and tip
            self.base_m.accumulate_force(total_force.scm(1-ct))
            self.tip_m.accumulate_force(total_force.scm(ct))
## current force is for test with rendering (draws blue force vectors)
            self.current_force = total_force
        else:
            self.current_force = None

    def renderforce(self, surf):
        """Draw (on a pygame surface) the hydro force exerted by this quad."""
        if self.current_force is not None:
            center = [int(x) for x in self.pos.ntuple()]
            pygame.draw.circle(surf, HYDRO_COLOR, center, 2, 0)
            tipvec = self.pos - self.current_force.scm(HYDRO_FORCE_SCALE)
            tip = [int(x) for x in tipvec.ntuple()]
            pygame.draw.line(surf, HYDRO_COLOR, center, tip, 2)


class SMHFish(object):
    """It's ostensibly a fish."""

    def __init__(self, head_data, body_data, tail_data, spring_k):
        # Placeholder for fish coordinate nodes
        self.numnodes = 12
        massnodes = list(range(self.numnodes))
        self.node_radius = NODE_RADIUS
        self.node_color = NODE_COLOR
        damping = DAMPING_COEFF # velocity-based damping coeff for mass nodes
        offset = Point2d(X_OFFSET, Y_OFFSET) # offset from head node

        ### Set up nodemasses ################################################
        # Head node (NOTE: No spritedata)
        head_mass = head_data[0]*MASS_SCALE
        massnodes[0] = DampedMass2d(offset, NODE_RADIUS, Point2d(0,0), head_mass, damping)

        # Body segment nodes
        x_local = 0
        index_right = 0
        quad_h = []
        for xlen, ywid, nmass, zhi in body_data:
            index_right += 2
            x_local += xlen
            # Right node (even index)
            nodepos = offset + Point2d(x_local, ywid).scm(SIZE_SCALE)
            massnodes[index_right] = DampedMass2d(nodepos, NODE_RADIUS, Point2d(0,0), nmass*MASS_SCALE, damping)
            # Left node (odd index)
            nodepos = offset + Point2d(x_local, -ywid).scm(SIZE_SCALE)
            massnodes[1 + index_right] = DampedMass2d(nodepos, NODE_RADIUS, Point2d(0,0), nmass*MASS_SCALE, damping)
            # Quad heights (needed later)
            quad_h.append(zhi)

        # Tail
        nodepos = offset + Point2d(x_local + tail_data[0], 0).scm(SIZE_SCALE)
        nmass = tail_data[1]
        massnodes[1] = DampedMass2d(nodepos, NODE_RADIUS, Point2d(0,0), nmass, damping)
        quad_h.append(tail_data[2])

        self.massnodes = tuple(massnodes)

        ### Set up muscle springs ###########################################
        springs = []
        muscle_k = spring_k['MUSCLE']
        squeeze_p = SQUEEZE
        for i, j in ((2,4), (3,5), (4,6), (5,7), (6,8), (7,9)):
            muscle = MuscleSpring2d(muscle_k, massnodes[i], massnodes[j], squeeze_p)
            springs.append(muscle)
            muscle.massnodes = (i,j)

        # Muscles only for now
        self.muscles = tuple(springs)
        self.num_muscles = len(springs)

        ### Set up non-muscle springs #######################################
        # Head springs
        for i, j in ((0,2), (0,3)):
            spring = IdealSpring2d(spring_k['HEAD'], massnodes[i], massnodes[j])
            springs.append(spring)
            spring.massnodes = (i,j)

        # Lateral springs
        for i, j in ((2,3), (4,5), (6,7), (8,9), (10,11)):
            spring = IdealSpring2d(spring_k['SOLID'], massnodes[i], massnodes[j])
            springs.append(spring)
            spring.massnodes = (i,j)

        # Springs 13 and 14: Better results with same spring constant as muscles.
        for i, j in ((8,10), (9,11)):
            spring = IdealSpring2d(spring_k['MUSCLE'], massnodes[i], massnodes[j])
            springs.append(spring)
            spring.massnodes = (i,j)

        # Tail springs
        for i, j in ((1,10), (11,1)):
            spring = IdealSpring2d(spring_k['TAIL'], massnodes[i], massnodes[j])
            springs.append(spring)
            spring.massnodes = (i,j)

        # Cross springs
        for i, j in ((2,5), (3,4), (4,7), (5,6), (6,9), (7,8), (9,10), (8,11)):
            spring = IdealSpring2d(spring_k['CROSS'], massnodes[i], massnodes[j])
            springs.append(spring)
            spring.massnodes = (i,j)

        # All springs, including muscles
        self.springs = tuple(springs)

        ### Set up surface quads for hydrodynamic force #####################
        hquadlist = []

        # Head quads
        front_h = head_data[1]
        back_h = quad_h.pop(0)
        # Right side
        hquad = HydroQuad2d(massnodes[2], back_h, massnodes[0], front_h)
        hquad.nodes = (2, 0)
        hquadlist.append(hquad)
        # Left side
        hquad = HydroQuad2d(massnodes[0], front_h, massnodes[3], back_h)
        hquad.nodes = (0, 3)
        hquadlist.append(hquad)

        # Body quads
        # There is some severe trickery going on here; see the fish anatomy.
        # We've read in the lenghts of each quad's base above; this puts them
        # onto the fish starting from the head and moving towards the tail.
        # The left side of each quad must point into the fish. Left/right
        # orientations in the comments are screen coordinates!
        for i in range(3, 11, 2):
            front_h = back_h
            back_h = quad_h.pop(0)
            # Right side (even index)
            hquad = HydroQuad2d(massnodes[i+1], back_h, massnodes[i-1], front_h)
            hquad.nodes = (i+1, i-1)
            hquadlist.append(hquad)
            # Left side (odd index)
            hquad = HydroQuad2d(massnodes[i], front_h, massnodes[i+2], back_h)
            hquad.nodes = (i, i+2)
            hquadlist.append(hquad)

        # Tail quads
        front_h = back_h
        back_h = quad_h.pop()
        # Right side
        hquad = HydroQuad2d(massnodes[1], back_h, massnodes[10], front_h)
        hquad.nodes = (1, 10)
        hquadlist.append(hquad)
        # Left side
        hquad = HydroQuad2d(massnodes[11], front_h, massnodes[1], back_h)
        hquad.nodes = (11, 1)
        hquadlist.append(hquad)

        self.hquads = tuple(hquadlist)

    def signal_muscles(self, group, direction):
        """Contract/flex muscle one of the muscles groups.

        Direction = 0 (contract left) or 1 (contract right).
        """
        if group == 1: # Front "turning" muscles
            pass
        if group == 2: # Midsection
            self.muscles[2].contract(direction)
            self.muscles[3].contract(1-direction)
        if group == 3: # Rear "swim" muscles
            self.muscles[4].contract(direction)
            self.muscles[5].contract(1-direction)

    def update(self, delta_t=1.0):
        """Update fish physics."""
        # Update Spring Forces
        for spring in self.springs:
            spring.exert_force()

        # Update hydroquads
        for quad in self.hquads:
            quad.exert_fluid_force(delta_t)

        # Update Nodes
        for node in self.massnodes:
            node.move(delta_t)

    def render(self, surf):
        """Render this fish."""
        # Manually render each spring
        for spring in self.springs:
            spring.render(surf)

        # Manually render each quad's hyrdo-force
        for quad in self.hquads:
            quad.renderforce(surf)

        # Manually render each massnode
        for node in self.massnodes:
            center = tuple(int(x) for x in node.pos.ntuple())
            pygame.draw.circle(surf, self.node_color, center, self.node_radius)

    def center_pos(self):
        """Center of position of all mass nodes except head/tail.

        TODO: Move this to fish_logger.py?
        """
        result = Point2d(0,0)
        for node in self.massnodes[2:]:
            result = result + node.pos
        return result.scm(1.0/self.numnodes)

if __name__ == "__main__":
    pygame.init()

    # Display constants
    DISPLAYSURF = pygame.display.set_mode(SCREEN_SIZE)
    pygame.display.set_caption('Spring-mass-hydro fish demo')
    BG_COLOR = (111, 145, 192)

    fish = SMHFish(HEAD_DATA, BODY_DATA, TAIL_DATA, SPRING_DATA)

    ## Stuff below is for swimming muscle updates ###############
    # TODO: Move this into the motor controller class
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

    xpos = fish.center_pos().ntuple()[0]
    t = 0
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

        # Render
        DISPLAYSURF.fill(BG_COLOR)
        fish.render(DISPLAYSURF)
        pygame.display.flip()
        ticks = ticks + 1
        
        # Time-keeping for average velocity
        t = t + 1
        if t == 1000: # Ignore start-up jitter and start here
            xpos = fish.center_pos().ntuple()[0]

    # Clean-up pygame and plot results
    pygame.quit()

    # Compute average x speed (over the appropriate interval)
    delta_x = (xpos - fish.center_pos().ntuple()[0])
    if t <= 1000:
        x_vel_avg = delta_x/t*UPDATE_SPEED
    else:
        x_vel_avg = delta_x/((t-1000)*UPDATE_SPEED)
        
    print('Average x speed was %.2f.' % x_vel_avg)


    #sys.exit()
