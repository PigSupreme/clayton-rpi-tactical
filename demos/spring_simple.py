#!/usr/bin/python
"""Springmass demo with gravity."""

# for python3 compat
from __future__ import unicode_literals
from __future__ import absolute_import
from __future__ import print_function
from __future__ import division

# TODO: Adjust this depending on where this file ends up
from sys import path
path.extend(['../vpoints', '../vehicle'])

import pygame
from pygame.locals import RLEACCEL, QUIT, MOUSEBUTTONDOWN
import pygame.mouse

from point2d import Point2d

INF = float('inf')

# BasePointMass2d defaults
import vehicle2d
vehicle2d.set_physics_defaults(MASS=1.0, MAXSPEED=INF, MAXFORCE=INF)

# Spring-Mass Extras
from springmass import DampedMass2d, IdealSpring2d

# Physics constants
NODE_RADIUS = 5
NODE_MASS = 10.0
DAMPING_COEFF = 1.0
SPRING_CONST = 15.0
UPDATE_SPEED = 0.005
# This assumes all nodes have the same mass
GRAV_ACCEL = 9.8
GRAVITY = Point2d(0, NODE_MASS*GRAV_ACCEL)

# Display size
SCREENSIZE = (800, 640)

if __name__ == "__main__":
    pygame.init()

    # Display setup
    DISPLAYSURF = pygame.display.set_mode(SCREENSIZE)
    pygame.display.set_caption('Spring-mass demo with gravity')
    bgcolor = 111, 145, 192

    # Mass image information
    imgt = pygame.Surface((2*NODE_RADIUS, 2*NODE_RADIUS))
    imgt.set_colorkey((0,0,0), RLEACCEL)
    rect = pygame.draw.circle(imgt, (1,1,1), (NODE_RADIUS, NODE_RADIUS), NODE_RADIUS, 0)

    # This is the actual mass
    NODE_DEFAULTS = (NODE_RADIUS, Point2d(0,0), NODE_MASS, DAMPING_COEFF, (imgt, rect))

    nodes = (DampedMass2d(Point2d(200,10), *NODE_DEFAULTS),
             DampedMass2d(Point2d(400,30), *NODE_DEFAULTS)
            )
    # These are for stationary ends of springs...
    # SimpleObstacles with no bounding radius nor spritedata
    hooks = (vehicle2d.SimpleObstacle2d(Point2d(100,100), 0),
             vehicle2d.SimpleObstacle2d(Point2d(600,200), 0),
             vehicle2d.SimpleObstacle2d(Point2d(400,450), 0)
            )
    springs = (IdealSpring2d(SPRING_CONST, hooks[0], nodes[0], 125),
               IdealSpring2d(SPRING_CONST, hooks[1], nodes[0], 125),
               IdealSpring2d(SPRING_CONST, hooks[2], nodes[1], 30),
               IdealSpring2d(SPRING_CONST, nodes[0], nodes[1], 75)
              )

    # Set-up pygame rendering
    rgroup = (nodemass.sprite for nodemass in nodes)
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

        # If left button down, position first mass at current mouse pointer
        if pygame.mouse.get_pressed()[0]: # left button
            nodes[0].pos = Point2d(*pygame.mouse.get_pos())
            nodes[0].vel = Point2d(0,0)
            nodes[1].vel = Point2d(0,0)
        # Otherwise, update physics as normal
        else:
            for nodem in nodes:
                nodem.move(UPDATE_SPEED)
                nodem.accumulate_force(GRAVITY)
            for spring in springs:
                spring.exert_force()

        allsprites.update(UPDATE_SPEED)

        # Render
        DISPLAYSURF.fill(bgcolor)
        # Render regular sprites (point masses)
        for spring in springs:
            spring.render(DISPLAYSURF)
        allsprites.draw(DISPLAYSURF)
        pygame.display.flip()

    # Clean-up here
    pygame.quit()
