#!/usr/bin/python
"""Springmass stuff; WIP."""

# for python3 compat
from __future__ import unicode_literals
from __future__ import absolute_import
from __future__ import print_function
from __future__ import division

import sys, pygame
from pygame.locals import RLEACCEL, QUIT, MOUSEBUTTONDOWN
import pygame.mouse

# TODO: Adjust this depending on where this file ends up.
sys.path.extend(['../vpoints', '../vehicle'])
from point2d import Point2d

INF = float('inf')

# BasePointMass2d defaults
import vehicle2d
vehicle2d.set_physics_defaults(MASS=5.0, MAXSPEED=INF, MAXFORCE=50000.0)

# Physics constants
NODE_RADIUS = 5
NODE_MASS = 10.0
DAMPING_COEFF = 1.0
SPRING_CONST = 15.0
UPDATE_SPEED = 0.005
GRAVITY = Point2d(0, NODE_MASS*9.8)

# Display size
SCREENSIZE = (800, 640)

class DampedMass2d(vehicle2d.BasePointMass2d):
    """A pointmass with linearly-damped velocity.

    Parameters
    ----------
    position: Point2d
        Center of mass, in screen coordinates.
    radius: float
        Bounding radius of the object.
    mass: float
        Mass of the object.
    velocity: Point2d
        Velocity vector, in screen coordinates. Initial facing matches this.
    damping:
        Proportionality constant: damping force = -damping * velocity 
    spritedata: list or tuple, optional
        Extra data used to create an associate sprite. See notes below.

    Notes
    -----
    This provides a minimal base class for a pointmass with bounding radius
    and heading aligned to velocity. Use move() for physics updates each
    cycle (including applying force).

    As we typically will be rendering these objects within some environment,
    the constructor provides an optional spritedata parameter that can be used
    to create an associated sprite. This is currently implemented using the
    PointMass2dSprite class above (derived from pygame.sprite.Sprite), but
    can be overridden by changing the _spriteclass attribute.

    Note: Positional parameters are in a different order thatn hydro_fish.py
    """
    def __init__(self, position, radius, mass, velocity, damping=DAMPING_COEFF, spritedata=None):
        vehicle2d.BasePointMass2d.__init__(self, position, radius, velocity, spritedata)
        self.mass = mass

    def move(self, delta_t=1.0):
        # Compute damping force
        self.accumulate_force(-self.vel.scm(DAMPING_COEFF))
        vehicle2d.BasePointMass2d.move(self, delta_t, None)

class StationaryMass2d(vehicle2d.BasePointMass2d):
    """A pointmass that stays in place, for attaching springs.
    
    Parameters
    ----------
    position: Point2d
        End of the attached spring will be fixed to this location.
    """  
    def __init__(self, position):
        vehicle2d.BasePointMass2d.__init__(self, position, 0, Point2d(0,0), None)

    def move(self, delta_t=1.0):
        """Does nothing, but necessary for pygame updates."""
        pass

class IdealSpring2d(object):
    """An ideal (massless, stiff) spring attaching two point masses.

    Parameters
    ----------
    spring_constant: positive float
        Linear Spring Constant (Hooke's Law).
    mass1: BasePointMass2d
        Point mass at the base of this spring; see Notes
    mass2: BasePointMass2d
        Point mass at the end of this spring; see Notes
    rest_length: float
        Natural length. If negative/unspecified, use distance between masses.

    Notes
    -----

    Since spring physics use vectors, the spring needs an implicit orientation
    (from mass1 to mass2). This orientation is used internally, but has no
    visible effect outside of the exert_force update.
    """
    def __init__(self, spring_constant, mass1, mass2, rest_length=-1):
        self.k = spring_constant
        # If rest_length is negative, use current distance between end masses
        if rest_length < 0:
            self.natlength = (mass1.pos - mass2.pos).norm()
        else:
            self.natlength = rest_length

        self.mass_base = mass1
        self.mass_tip = mass2
        
        self.displacement = self.mass_tip.pos - self.mass_base.pos
        self.curlength = self.displacement.norm()

    def exert_force(self):
        """Compute spring force and and apply it to the attached masses."""
        self.displacement = self.mass_tip.pos - self.mass_base.pos
        self.curlength = self.displacement.norm()
        magnitude = self.k*(1 - self.natlength/self.curlength)
        self.mass_base.accumulate_force(self.displacement.scm(magnitude))
        self.mass_tip.accumulate_force(self.displacement.scm(-magnitude))

    def render(self, surf):
        """Draw this spring, see below.
        
        Parameters
        ----------
        surf: pygame.Surface:
            The spring will be rendered on this surface. See Notes.
            
        Notes
        -----
        Springs are green when stretched, red when compressed. In either case,
        a brighter color means further deviation from natural length.
        """
        self.displacement = self.mass_tip.pos - self.mass_base.pos
        self.curlength = self.displacement.norm()
        scale = self.natlength/self.curlength
        if scale > 1: # Shade green for stretched springs
            spcolor = min(255, 64*scale), 0, 0
        else: # Shade red for compressed springs
            spcolor = 0, min(255, 64*scale), 0
        start = self.mass_base.pos.ntuple()
        stop = self.mass_tip.pos.ntuple()
        pygame.draw.line(surf, spcolor, start, stop, 2)


if __name__ == "__main__":
    pygame.init()

    # Display setup
    screen = pygame.display.set_mode(SCREENSIZE)
    pygame.display.set_caption('Single mass + two springs + gravity')
    bgcolor = 111, 145, 192
    # Mass image information
    imgt = pygame.Surface((2*NODE_RADIUS, 2* NODE_RADIUS))
    imgt.set_colorkey((0,0,0), RLEACCEL)
    rect = pygame.draw.circle(imgt, (1,1,1), (NODE_RADIUS, NODE_RADIUS), NODE_RADIUS, 0)
    # This is the actual mass
    nodem = DampedMass2d(Point2d(200,10), NODE_RADIUS, NODE_MASS , Point2d(0,0), DAMPING_COEFF, (imgt, rect))
    # These are for stationary ends of springs
    hooks = (StationaryMass2d(Point2d(200,300)),
             StationaryMass2d(Point2d(600,300)),
#             StationaryMass2d(Point2d(300,450))
             )
    springs = (IdealSpring2d(SPRING_CONST, hooks[0], nodem, 125),
               IdealSpring2d(SPRING_CONST, hooks[1], nodem, 125),
#               IdealSpring2d(SPRING_CONST, hooks[2], nodem, 30),
               )

    # List of nodes only, for later use
    rgroup = (nodem.sprite,)

    # Set-up pygame rendering
    allsprites = pygame.sprite.RenderPlain(rgroup)

    b_running = True

    ############  Main Loop  ######################
    while b_running:
        for event in pygame.event.get():
            if event.type == QUIT:
                b_running = False

            if event.type == MOUSEBUTTONDOWN:
                if event.button == 3:  # Right button
                    b_running = False
                    
        # If left button down, position mass at current mouse pointer
        if pygame.mouse.get_pressed()[0]: # left button
            nodem.pos = Point2d(*pygame.mouse.get_pos())
            nodem.vel = Point2d(0,0)
        # Otherwise, update physics as normal
        else:
            nodem.move(UPDATE_SPEED)
            for spring in springs:
                spring.exert_force()
            nodem.accumulate_force(GRAVITY)
        
        allsprites.update(UPDATE_SPEED)        

        # Render
        screen.fill(bgcolor)
        # Render regular sprites (point masses)
        for spring in springs:
            spring.render(screen)
        allsprites.draw(screen)
        pygame.display.flip()


    # Clean-up here
    pygame.time.delay(500)
    pygame.quit()
    sys.exit()
