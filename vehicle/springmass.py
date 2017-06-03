#!/usr/bin/python
"""Springmass stuff; WIP."""

# for python3 compat
from __future__ import unicode_literals
from __future__ import absolute_import
from __future__ import print_function
from __future__ import division

# TODO: Adjust this depending on where this file ends up.
from sys import path
path.append('../vpoints')
import point2d

INF = float('inf')

# BasePointMass2d defaults
import vehicle2d
vehicle2d.set_physics_defaults(MASS=1.0, MAXSPEED=INF, MAXFORCE=INF)

# Physics constants
NODE_RADIUS = 5
NODE_MASS = 10.0
DAMPING_COEFF = 1.0
SPRING_CONST = 15.0
UPDATE_SPEED = 0.005

# Needed for Spring rendering
import pygame.draw

class DampedMass2d(vehicle2d.BasePointMass2d):
    """A pointmass with linearly-damped velocity.

    Parameters
    ----------
    position: Point2d
        Center of mass, in screen coordinates.
    radius: float
        Bounding radius of the object.
    velocity: Point2d
        Velocity vector, in screen coordinates. Initial facing matches this.
    mass: float
        Mass of the object.
    damping:
        Proportionality constant: damping force = -damping * velocity
    spritedata: list or tuple, optional
        Extra sprite data; see BasePointMass2d for details.

    Notes
    -----
    This is a simple extension of BasePointMass2d that adds a damping force
    proportional to velocity.

    TODO: Positional parameters are in a different order thatn hydro_fish.py
    """
    def __init__(self, position, radius, velocity,
                 mass=NODE_MASS, damping=DAMPING_COEFF, spritedata=None):
        vehicle2d.BasePointMass2d.__init__(self, position, radius, velocity, spritedata)
        self.mass = mass
        self.damping = damping

    def move(self, delta_t=1.0, force=None):
        """Updates position, velocity, and acceleration (with damping).

        Parameters
        ----------
        delta_t: float
            Time increment since last move.
        force_vector: Point2d or None (default)
            Additional non-damping force to apply; see Notes below.

        Notes
        -----
        Applied force behaves as in BasePointMass2d.move(); see notes there.
        This class adds a damping force, proportional to velocity, each update.
        """
        if force is not None:
            force = force - self.vel.scm(self.damping)
        else:
            self.accumulate_force(-self.vel.scm(self.damping))
        vehicle2d.BasePointMass2d.move(self, delta_t, force)

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
    print("Two-dimension spring-mass classes. Import this elsewhere.")
    