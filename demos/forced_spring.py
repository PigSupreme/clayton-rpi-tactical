#!/usr/bin/python
"""Springmass stuff; WIP."""

# for python3 compat
from __future__ import unicode_literals
from __future__ import absolute_import
from __future__ import print_function
from __future__ import division

from math import cos, sin

import pygame
from pygame.locals import RLEACCEL, QUIT, MOUSEBUTTONDOWN
import pygame.mouse

# TODO: Adjust this depending on where this file ends up.
from sys import path
path.extend(['../vpoints', '../vehicle'])
from point2d import Point2d

INF = float('inf')

# BasePointMass2d defaults
import vehicle2d
vehicle2d.set_physics_defaults(MASS=5.0, MAXSPEED=INF, MAXFORCE=INF)

# Spring-Mass Extras
from springmass import DampedMass2d, IdealSpring2d

# Physics constants
NODE_RADIUS = 5
NODE_MASS = 10.0
DAMPING_COEFF = 4.0
SPRING_CONST = 15.0
UPDATE_SPEED = 0.005

# Positive y is downward in screen coordinates
G_ACCEL = 9.8
GRAVITY = Point2d(0, NODE_MASS*G_ACCEL)

# Amplitude and frequency of the "fixed" end of the spring.
FORCING_AMPLITUDE = 40
FORCING_FREQ = 2.0

# Display size
SCREENSIZE = (800, 640)
FONT_SIZE = 32

if __name__ == "__main__":
    pygame.init()

    # Display setup
    screen = pygame.display.set_mode(SCREENSIZE)
    pygame.display.set_caption('Spring with oscillating "fixed" end and attached mass.')
    bgcolor = 111, 145, 192
    # Mass image information
    imgt = pygame.Surface((2*NODE_RADIUS, 2*NODE_RADIUS))
    imgt.set_colorkey((0,0,0), RLEACCEL)
    rect = pygame.draw.circle(imgt, (1,1,1), (NODE_RADIUS, NODE_RADIUS), NODE_RADIUS, 0)
    # This is the actual mass
    nodem = DampedMass2d(Point2d(400,400), NODE_RADIUS, Point2d(0,0),
                         NODE_MASS, DAMPING_COEFF, (imgt, rect))

    # Spring is attached to this
    hooks = (vehicle2d.SimpleObstacle2d(Point2d(400,200), 0),)

    # This is the spring
    springs = (IdealSpring2d(SPRING_CONST, hooks[0], nodem, 150),)

    # Set-up pygame rendering. This is usually used to let pygame automatically
    # manage large groups of sprites (via the update() and draw() methods). See
    # vehicle2d.PointMass2dSprite class for further details.
    rgroup = (nodem.sprite,)
    allsprites = pygame.sprite.RenderPlain(rgroup)

    # Added stuff for plotting
    forcing = []
    yvals = []
    t = 0
    phase = 0.0

    dfont = pygame.font.SysFont(pygame.font.get_default_font(), FONT_SIZE)
    MSG_TEXT = ("Hold left mouse to position mass; right-click to exit.",
                "Release left mouse to release mass."
               )
    MSG_SURF = [dfont.render(MSG_TEXT[i], True, (0,0,0)) for i in range(len(MSG_TEXT))]

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
            mouse_state = 1 # Used to suppress physics updates below

        # Otherwise, update physics as normal
        else:
            mouse_state = 0 # Used to signal physics updates below
            # This applies velocity-based damping (from DampedMass2d)
            # and in turn called PointMass2d.move(), which updates position,
            # velocity, and acceleration based on current force.
            nodem.move(UPDATE_SPEED)
            # Constant force due to gravity.
            nodem.accumulate_force(GRAVITY)

            # Oscillate the "fixed" hook
            hooks[0].pos = Point2d(400,200 + FORCING_AMPLITUDE*sin(phase))
            phase = phase + UPDATE_SPEED*FORCING_FREQ

            # Each spring imparts a force to its attached masses,
            # based on current displacement from its natural length.
            for spring in springs:
                spring.exert_force()

        # This updates sprite images only, so do it regardless of physics.
        allsprites.update(UPDATE_SPEED)

        # Record position for later plotting
        (xval, yval) = nodem.pos[:]
        forcing.append(hooks[0].pos[1])
        yvals.append(yval)
        t = t + 1

        ### Rendering starts here ###
        screen.fill(bgcolor)
        # Draw the springs manually (they don't have an attached sprite)
        for spring in springs:
            spring.render(screen)
        # Draw the forcing hooks
        for hook in hooks:
            (x,y) = hook.pos[:]
            pygame.draw.line(screen, (0,0,0), (x-20,y), (x+20,y))
        # Let Pygame draw the point-mass sprites
        allsprites.draw(screen)

        # Display instructional text...
        screen.blit(MSG_SURF[mouse_state], (10,10))
        # ...and current position of mass
        info_surf = dfont.render("(x,y) = (%d, %d)" % nodem.pos[:], True, (0,0,0))
        screen.blit(info_surf, (10, SCREENSIZE[1]-30))

        # Double-buffering (a standard trick for speedy rendering)
        pygame.display.flip()

    # Clean-up here
    pygame.time.delay(500)
    pygame.quit()
#    matplotlib.pylab.show(matplotlib.pylab.plot(xvals,'r',yvals,'g'))

    # Plot results
    import matplotlib.pyplot as plt

    tr = range(0,t)
    plt.subplot(3, 1, 1)
    plt.plot(forcing)
    plt.ylabel('Vertical\n displacement')

    plt.subplot(3, 1, 2)
    plt.plot(yvals)
    plt.ylabel('y-coordinate')

    plt.subplot(3, 1, 3)
    plt.plot(tr, forcing, tr, yvals)
    plt.ylabel('Combined')

    plt.show()
