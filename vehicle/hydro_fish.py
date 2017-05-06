#!/usr/bin/python
"""Springmass fish with hydro forces. Modified from fish_no_hydro.py"""

# for python3 compat
from __future__ import unicode_literals
from __future__ import absolute_import
from __future__ import print_function
from __future__ import division

import sys, pygame
from pygame.locals import RLEACCEL, QUIT, MOUSEBUTTONDOWN

# TODO: Adjust this depending on where this file ends up.
sys.path.extend(['../vpoints', '../vehicle'])
from point2d import Point2d

# BasePointMass2d defaults
import vehicle2d
vehicle2d.POINTMASS2D_MASS = 5
vehicle2d.POINTMASS2D_MAXSPEED = 80
vehicle2d.POINTMASS2D_MAXFORCE = 50000

# Math defaults
from math import sqrt
INF = float('inf')

# Fish coefficients (coefishents??)
DAMPING_COEFF = 10
SPRING_CONST = 3
MUSCLE_K = 90
SOLIDS_K = 100
CROSS_K = 150
TAIL_K = 80
FREQ = 240
SQUEEZE = 0.88
HYDRO_FORCE_SCALE = 0.02
UPDATE_SPEED = 0.02


class SpringMass2d(vehicle2d.BasePointMass2d):
    """A point mass that can accumulate several forces and apply all at once.
    
    TODO: Rename this to something more general.
    """
    def __init__(self, position, mass, velocity, spritedata=None):
        radius = 5
        vehicle2d.BasePointMass2d.__init__(self, position, radius, velocity, spritedata)
        self.mass = mass
        self.accumulated_force = Point2d(0,0)
        
    def accumulate_force(self, force_vector):
        """Add a new force to what's already been acculumated."""
        self.accumulated_force = self.accumulated_force + force_vector
        
    def apply_force(self, delta_t=1.0):
        # Compute damping force
        force = self.accumulated_force - self.vel.scale(DAMPING_COEFF)
        
        self.move(delta_t, force)
        self.accumulated_force = Point2d(0,0)
        

class IdealSpring2d(object):
    """An ideal (massless, stiff) spring attaching two point masses.
    
    Parameters
    ----------
    spring_constant: positive float
        Linear Spring Constant (Hooke's Law).
    rest_length: float
        Natural length. If negative, use the current distance between masses.  
    mass1: BasePointMass2d
        Point mass at the base of this spring; see Notes
    mass2: BasePointMass2d
        Point mass at the end of this spring; see Notes
    
    Notes
    -----
    
    Since spring physics use vectors, the spring needs an implicit orientation
    (from mass1 to mass2). This orientation is used internally, but has no
    visible effect outside of the exert_force update.
    """
    def __init__(self, spring_constant, rest_length, mass1, mass2):
        self.k = spring_constant
        # Give negative rest_length to use current distance between masses
        if rest_length < 0:
            self.natlength = (mass1.pos - mass2.pos).norm()
        else:
            self.natlength = rest_length

        self.mass_base = mass1
        self.mass_tip = mass2
        
    def exert_force(self):
        """Compute spring force and and apply it to the attached masses."""
        self.displacement = self.mass_tip.pos - self.mass_base.pos
        self.curlength = self.displacement.norm()        
        self.curscale = self.natlength/self.curlength
        magnitude = self.k*(1 - self.curscale)
        self.mass_base.accumulate_force(self.displacement.scale(magnitude))
        self.mass_tip.accumulate_force(self.displacement.scale(-magnitude))


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
        IdealSpring2d.__init__(self, spring_constant, -1, mass1, mass2)
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
    pass


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
        # This is computed using center of mass of a trapezoid
        if base_height == tip_height:
            self.center_t = 0.5
        else:
            numer = sqrt(2*(tip_height**2 + base_height**2)) - 2*base_height
            self.center_t = numer/(2*(tip_height - base_height))

    def exert_fluid_force(self, delta_t=1.0):
        """Compute and apply force to end masses based on surface velocity.
        
        TODO: Better explain the fluid dynamics being used here.
        """
        # Compute position and velocity of center of area
        ct = self.center_t  # For convenience in formulas belotw
        self.pos = self.base_m.pos.scale(1-ct) + self.tip_m.pos.scale(ct)
        self.vel = self.base_m.vel.scale(1-ct) + self.tip_m.vel.scale(ct)
        
        # Compute total fluidic force
        front_vec = self.tip_m.pos - self.base_m.pos
        normal_in = front_vec.left_normal()
        dotp = self.vel * normal_in
        
        # Only apply force if center is moving in an outward direction from body
        # Force is proportional (somehow...) to volume of displaced fluid
        area = 0.5*(self.base_h + self.tip_h)*front_vec.norm()
        if dotp < 0:
            # Compute the area of this quad (trapezoid)
            area = 0.5*(self.base_h + self.tip_h)*front_vec.norm()
            total_force = normal_in.scale(-dotp*area*delta_t/normal_in.sqnorm())
            # Apply to masses at base and tip
            self.base_m.accumulate_force(total_force.scale(1-ct))
            self.tip_m.accumulate_force(total_force.scale(ct))
## current force is for test with rendering
            self.current_force = total_force.scale(HYDRO_FORCE_SCALE)
        else:
            self.current_force = None
        

if __name__ == "__main__":
    pygame.init()

    # Display constants
    size = sc_width, sc_height = 800, 640
    screen = pygame.display.set_mode(size)
    pygame.display.set_caption('Spring-mass demo')
    bgcolor = 111, 145, 192

    # Fish coordinate nodes
    MASS_SCALE = 15
    SIZE_SCALE = 5
    X_OFFSET = 100
    nodedata = [(X_OFFSET+0,0,0.5), (X_OFFSET+62,0,0.004)]  # Head and tail
    for i, j, m in [(8,4,6.6), (20,6,11.0), (35,6,8.6), (47,4,1.1), (57,2,1.1)]:
        nodedata.append((X_OFFSET+i,j,m*MASS_SCALE))
        nodedata.append((X_OFFSET+i,-j,m*MASS_SCALE))
    numnodes = len(nodedata)
    img = list(range(numnodes))
    rec = list(range(numnodes))
        
    # Set-up Node Sprites in their initial positions
    obj = []
    img = []
    rec = []
    for i, j, m in nodedata:
        imgt = pygame.Surface((10,10))
        imgt.set_colorkey((0,0,0), RLEACCEL)
        rect = pygame.draw.circle(imgt,(1,1,1),(5,5),5,0)
        img.append(imgt)
        rec.append(rect)
        nodet = SpringMass2d(Point2d(i+50,j+75).scale(SIZE_SCALE), m , Point2d(0,0), (imgt, rect))
        obj.append(nodet)
        
    # List of nodes only, for later use
    nodelist = obj[:]
    rgroup = [node.sprite for node in obj]
    
    # Set-up pygame rendering for all objects
    allsprites = pygame.sprite.RenderPlain(rgroup)

    # Set up springs
    springs = []
    edge_muscles = [(2,4), (4,6), (6,8), (3,5), (5,7), (7,9)]
    muscle_k = MUSCLE_K
    for edge in edge_muscles:
        i, j = edge
        springs.append(MuscleSpring2d(muscle_k, nodelist[i], nodelist[j], SQUEEZE))

    # List of muscles for later use
    muscles = springs[:]
    muscle_count = len(springs)
        
    edge_solids = [(0,2), (0,3), (2,3), (4,5), (6,7), (8,9), (10,11), (8,10), (9,11)]
    solids_k = SOLIDS_K
    for edge in edge_solids:
        i, j = edge
        springs.append(IdealSpring2d(solids_k, -1, nodelist[i], nodelist[j]))
        
    edge_tail = [(1,10), (11,1)]
    tail_k = TAIL_K
    for edge in edge_tail:
        i, j = edge
        springs.append(IdealSpring2d(tail_k, -1, nodelist[i], nodelist[j]))
        
    edge_cross = [(2,5), (3,4), (4,7), (5,6), (6,9), (7,8), (9,10), (8,11)]
    cross_k = CROSS_K
    for edge in edge_cross:
        i, j = edge
        springs.append(IdealSpring2d(cross_k, -1, nodelist[i], nodelist[j]))

    ################################        
    # This fish is hyyyyydromatic...
    ################################
    quaddata = [(1,10,4.3,0.6),(10,8,1,2),(8,6,2,3),(6,4,3,3),(4,2,3,2),(2,0,2,0),
                (11,1,0.6,4.3),(9,11,2,1),(7,9,3,2),(5,7,3,3),(3,5,2,3),(0,3,0,2)
                ]

    hquadlist = []
    for b,t,bh,th in quaddata:
        hquadlist.append(HydroQuad2d(nodelist[b], bh, nodelist[t], th))
    
    ############  Main Loop  ######################

    freq = FREQ
    ticks = 0
    ticks2 = freq//2
    muscles[1].contract(1)
    muscles[4].contract(0)
    
    muscles[2].contract(0)
    muscles[5].contract(1)
    
    while 1:
        for event in pygame.event.get():
            if event.type in [QUIT, MOUSEBUTTONDOWN]:
                pygame.quit()
                sys.exit()

        # Squeeze Test
        if ticks >= freq:
            ticks = 0
            for i in [1,4]:
                curcon = muscles[i].contracted
                muscles[i].contract(1 - curcon)         
        if ticks2 >= freq:
            ticks2 = 0
            for i in [2,5]:
                curcon = muscles[i].contracted
                muscles[i].contract(1 - curcon) 

        # Update Spring Forces
        for spring in springs:
            spring.exert_force()
            
        # Update hydroquads
        for quad in hquadlist:
            quad.exert_fluid_force()

        # Update Nodes
        for node in nodelist:
            node.apply_force(UPDATE_SPEED)

        # Update Sprites (via pygame sprite group update)
        allsprites.update(UPDATE_SPEED)

        # Shift sprites so that node 0 stays fixed
#        old_nose = nodelist[0].pos
#        nose_tip = Point2d(sc_width/4, sc_height/2)
#        for node in nodelist:
#            node.pos = node.pos - old_nose + nose_tip

        # Render
        screen.fill(bgcolor)
        
        # Manually render each spring
        for spring in springs:
            scale = spring.curscale
            if scale > 1: # Shade green for stretched springs
                spcolor = min(255, 64*scale), 0, 0
            else: # Shade red for compressed springs
                spcolor = 0, min(255, 64//scale), 0
            start = spring.mass_base.pos.ntuple()
            stop = spring.mass_tip.pos.ntuple()
            pygame.draw.line(screen, spcolor, start, stop, 2)

        # Manually render each quad's hyrdo-force
        for quad in hquadlist:
            if quad.current_force is not None:
                center = [int(x) for x in quad.pos.ntuple()]
                pygame.draw.circle(screen,(0,90,190),center,3,0)
                tipvec = quad.pos - quad.current_force
                tip = [int(x) for x in tipvec.ntuple()]
                pygame.draw.line(screen, (0,90,190), center, tip, 2)
            
        # Render regular sprites (point masses)
        allsprites.draw(screen)            
        pygame.display.flip()
        ticks = ticks + 1

    # Clean-up here
    pygame.time.delay(2000)
    pygame.quit()
    sys.exit()
    