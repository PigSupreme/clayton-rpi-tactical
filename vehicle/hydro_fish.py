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

# Fish coefficients (coefishents??)
NODE_RADIUS = 0
MASS_SCALE = 12
SIZE_SCALE = 6
DAMPING_COEFF = 10
MUSCLE_K = 80
SOLIDS_K = 90
CROSS_K = 200
TAIL_K = 70

HEAD_MASS = 0.5
# (Length, half-width, nodemass) for each segment
BODY_DATA = [(8,4,6.6), (12,6,11.0), (15,6,8.6), (12,4,1.1), (10,2,1.1)]
# (Length, nodemass) of tail
TAIL_DATA = (5,0.004)

SQUEEZE = 0.89
FREQ = 180

HYDRO_FORCE_MULT = 45# Actual force multiplier
HYDRO_FORCE_SCALE = 0.02 # For rendering only
HYDRO_COLOR = (0,90,190)

X_OFFSET = 400
Y_OFFSET = 400

UPDATE_SPEED = 0.02

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

        # Location of center of mass as a proportion of total segment length
        # used in standard parametric equations.

        if base_height == tip_height:
            # Rectangles don't work in the formula below.
            self.center_t = 0.5
        else:
            # Otherwise, use center of mass of a trapezoid.
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
        # Force is proportional (somehow...) to volume of displaced fluid
        if dotp < 0:
            # Compute the area of this quad (trapezoid)
            area = 0.5*(self.base_h + self.tip_h)*contour_vec.norm()
            total_force = normal_in.scm(-dotp*area*delta_t*HYDRO_FORCE_MULT/normal_in.sqnorm())
            # Apply to masses at base and tip
            self.base_m.accumulate_force(total_force.scm(1-ct))
            self.tip_m.accumulate_force(total_force.scm(ct))
## current force is for test with rendering (draws blue force vectors)
            self.current_force = total_force
        else:
            self.current_force = None

    def renderforce(self, surf):
        """Draw the hydro force exerted by this quad."""
        if self.current_force is not None:
            center = [int(x) for x in self.pos.ntuple()]
            pygame.draw.circle(surf, HYDRO_COLOR, center, 3, 0)
            tipvec = self.pos - self.current_force.scm(HYDRO_FORCE_SCALE)
            tip = [int(x) for x in tipvec.ntuple()]
            pygame.draw.line(surf, HYDRO_COLOR, center, tip, 2)


class SMHFish(object):
    """It's ostensibly a fish."""

    def __init__(self, head_mass, body_data=None, tail_data=None):
        # Placeholder for fish coordinate nodes
        self.numnodes = 12
        massnodes = list(range(self.numnodes))
        damping = DAMPING_COEFF # velocity-based damping coeff for mass nodes
        offset = Point2d(X_OFFSET, Y_OFFSET) # offset from head node
        # Set-up Node Sprites in their initial positions
#        massnodes = []
#        img = []
#        rec = []

        # Head node (NOTE: No spritedata)
        massnodes[0] = DampedMass2d(offset, NODE_RADIUS, Point2d(0,0), head_mass*MASS_SCALE, damping)

        x_local = 0
        index_right = 0
        for xlen, ywid, nmass in body_data:
            index_right += 2
            x_local += xlen
            # Right node (even index)
            nodepos = offset + Point2d(x_local, ywid).scm(SIZE_SCALE)
            massnodes[index_right] = DampedMass2d(nodepos, NODE_RADIUS, Point2d(0,0), nmass*MASS_SCALE, damping)
            # Left node (odd index)
            nodepos = offset + Point2d(x_local, -ywid).scm(SIZE_SCALE)
            massnodes[1 + index_right] = DampedMass2d(nodepos, NODE_RADIUS, Point2d(0,0), nmass*MASS_SCALE, damping)
        # Tail
        nodepos = offset + Point2d(x_local + tail_data[0], 0).scm(SIZE_SCALE)
        nmass = tail_data[1]
        massnodes[1] = DampedMass2d(nodepos, NODE_RADIUS, Point2d(0,0), nmass, damping)

        # Prints initial location of each node        
        i = 0
        for node in massnodes:
            print('%d : %s' % (i, node.pos))
            i += 1

        # Set up muscle springs
        springs = []
        muscle_k = MUSCLE_K
        squeeze_p = SQUEEZE
        for i, j in ((2,4), (3,5), (4,6), (5,7), (6,8), (7,9)):
            springs.append(MuscleSpring2d(muscle_k, massnodes[i], massnodes[j], squeeze_p))

        # List of muscles for later use
        muscles = springs[:]

        edge_solids = [(0,2), (0,3), (2,3), (4,5), (6,7), (8,9), (10,11), (8,10), (9,11)]
        # Stiffer head springs
        for edge in edge_solids[:2]:
            i, j = edge
            springs.append(IdealSpring2d(SOLIDS_K*4, massnodes[i], massnodes[j]))
        # Other 
        for edge in edge_solids[2:]:
            i, j = edge
            springs.append(IdealSpring2d(SOLIDS_K, massnodes[i], massnodes[j]))

        edge_tail = [(1,10), (11,1)]
        for edge in edge_tail:
            i, j = edge
            springs.append(IdealSpring2d(TAIL_K, massnodes[i], massnodes[j]))

        edge_cross = [(2,5), (3,4), (4,7), (5,6), (6,9), (7,8), (9,10), (8,11)]
        for edge in edge_cross:
            i, j = edge
            springs.append(IdealSpring2d(CROSS_K, massnodes[i], massnodes[j]))

        self.massnodes = tuple(massnodes)
        self.springs = tuple(springs)
        self.muscles = tuple(muscles)

        ################################
        # This fish is hyyyyydromatic...
        ################################
        quaddata = [(1,10,5.3,0.6),(10,8,1,2),(8,6,2,3),(6,4,3,3),(4,2,3,2),(2,0,2,0.1),
                    (11,1,0.6,5.3),(9,11,2,1),(7,9,3,2),(5,7,3,3),(3,5,2,3),(0,3,0.1,2)
                   ]

        hquadlist = []
        # Note the change in parameter order between above data and HydroQuad2d()
        for b,t,bh,th in quaddata:
            hquadlist.append(HydroQuad2d(massnodes[b], bh, massnodes[t], th))
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

        # Update Sprites (via pygame sprite group update)
#        self.allsprites.update(delta_t)

    def render(self, surf):
        """Render this fish."""
        # Manually render each spring
        for spring in self.springs:
            spring.render(surf)

        # Manually render each quad's hyrdo-force
        for quad in self.hquads:
            quad.renderforce(surf)

        # Render regular sprites (point masses)
#        self.allsprites.draw(surf)

    def center_pos(self):
        """Center of position of all mass nodes."""
        result = Point2d(0,0)
        for node in self.massnodes:
            result = result + node.pos
        return result.scm(1/self.numnodes)

if __name__ == "__main__":
    pygame.init()

    # Display constants
    size = sc_width, sc_height = 800, 640
    screen = pygame.display.set_mode(size)
    pygame.display.set_caption('Spring-mass-hydro fish demo')
    bgcolor = (111, 145, 192)

    fish = SMHFish(HEAD_MASS, BODY_DATA, TAIL_DATA)

    ## Stuff below is for swimming muscle updates
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

    # Additional stuff for plotting
    nls = ([],[])
    als = ([],[],[],[])
    xpos = fish.center_pos()[0]
    xvel = []
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

        # Get spring lengths for later plots
        # Midection
        nls[0].append(fish.muscles[2].natlength) # Natural, right
        als[0].append(fish.muscles[2].curlength) # Actual, right
        nls[1].append(fish.muscles[3].natlength) # Natural, left
        als[1].append(fish.muscles[3].curlength) # Actual, left
        # Rear swim
        als[2].append(fish.muscles[4].curlength) # Actual, right
        als[3].append(fish.muscles[5].curlength) # Actual, left

        xposnew = fish.center_pos().ntuple()[0]
        xvel.append((xposnew - xpos)/UPDATE_SPEED)
        xpos = xposnew

        # Render
        screen.fill(bgcolor)
        fish.render(screen)
        pygame.display.flip()
        ticks = ticks + 1

    # Clean-up pygame and plot results
    pygame.quit()

    import matplotlib.pyplot as plt
    plt.subplot(3, 1, 1)
    plt.plot(nls[0],'b', als[0],'g',als[1],'r')
    plt.legend(['Signal','R','L'])
    plt.ylabel('Midsection')

    plt.subplot(3, 1, 2)
    plt.plot(als[2],'g',als[3],'r')
    plt.legend(['R','L'])
    plt.ylabel('Rear swim')

    plt.subplot(3, 1, 3)
    plt.plot(xvel)
    plt.ylabel('x velocity\n of center')

    xavg = sum(xvel)/len(xvel)
    print('Average x velocity of center: %.2f' % xavg)

    plt.show()
    #sys.exit()
