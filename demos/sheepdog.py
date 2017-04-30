#!/usr/bin/env python
"""Flocking vehicle demo."""

# for python3 compat
from __future__ import unicode_literals
from __future__ import absolute_import
from __future__ import print_function
from __future__ import division

import sys, pygame
from pygame.locals import QUIT, MOUSEBUTTONDOWN
from random import randint, shuffle

# Note: Adjust this depending on where this file ends up.
sys.path.append('..')
from vpoints.point2d import Point2d

from vehicle.vehicle2d import load_pygame_image
from vehicle.vehicle2d import SimpleVehicle2d, SimpleObstacle2d, BaseWall2d

import steering
steering.FLOCKING_RADIUS_MULTIPLIER = 1.5
steering.EVADE_PANIC_SQ = 180**2

UPDATE_SPEED = 0.5

if __name__ == "__main__":
    pygame.init()

    # Display constants
    size = sc_width, sc_height = 1080, 960
    screen = pygame.display.set_mode(size)
    pygame.display.set_caption('Flocking and pursuit demo')
    bgcolor = 111, 145, 192

    # Sprite images and pygame rectangles
    numveh = 30
    numobs = 15
    img = list(range(numveh+numobs))
    rec = list(range(numveh+numobs))

    # Vehicle Sprites
    img[0], rec[0] = load_pygame_image('../images/ypig.png', -1)
    for i in range(1, numveh):
        img[i], rec[i] = load_pygame_image('../images/gpig.png', -1)
        
    # Vehicle Physics
    pos = [Point2d(randint(30, sc_width-30), randint(30, sc_height-30)) for i in range(numveh)]
    pos[0] = Point2d(sc_width/2, sc_height/2)
    vel = Point2d(5.0,0).rotated_by(147*i, True)
    
    # List of vehicles and their associated sprites
    obj = [SimpleVehicle2d(pos[i], 50, vel, (img[i], rec[i])) for i in range(numveh)]
    rgroup = [veh.sprite for veh in obj]

    # List of vehicles only, for later use
    vehlist = obj[:]

    # Static obstacles
    for i in range(numveh, numveh + numobs):
        img[i], rec[i] = load_pygame_image('../images/circle.png', -1)

    # Static obstacle Physics
    yoffset = sc_height//(numobs+1)
    yvals = list(range(yoffset, sc_height-yoffset, yoffset))
    yvals.append(yoffset)
    shuffle(yvals)
    for i in range(numveh, numveh + numobs):
        offset = (i+1.0-numveh)/(numobs+1)
        rany = yvals[i-numveh]
        pos.append(Point2d(offset*sc_width, rany))
        obstacle = SimpleObstacle2d(pos[i], 10, (img[i], rec[i]))
        obj.append(obstacle)
        rgroup.append(obstacle.sprite)
        
    # List of non-wall obstacles only, for later use
    obslist = obj[numveh:]

    # Static Walls: Only near screen boundary
    walllist = (BaseWall2d((sc_width//2, 10), sc_width-20, 4, Point2d(0,1)),
                 BaseWall2d((sc_width//2, sc_height-10), sc_width-20, 4, Point2d(0,-1)),
                 BaseWall2d((10, sc_height//2), sc_height-20, 4, Point2d(1,0)),
                 BaseWall2d((sc_width-10,sc_height//2), sc_height-20, 4, Point2d(-1,0)))
    obj.extend(walllist)
    rgroup.extend([wall.sprite for wall in walllist])

    # Set-up pygame rendering for all objects
    allsprites = pygame.sprite.RenderPlain(rgroup)

    ### Steering behaviours ###
    dog = vehlist[0]
    dog.maxspeed = 10.0
    dog.radius = 40
    dog.steering.set_target(AVOID=obslist, WALLAVOID=[25, walllist])
    dog.steering.set_target(SEPARATE=vehlist, ALIGN=vehlist)
    dog.steering.set_target(WANDER=(200, 25, 6))

    # Flocking demo fails to celebrate its sheep diversity...
    for sheep in vehlist[1:]:
        sheep.maxspeed = 8.0
        sheep.maxforce = 6.0
        sheep.radius = 40
        sheep.steering.set_target(AVOID=obslist, WALLAVOID=[25, walllist])
        sheep.steering.set_target(SEPARATE=vehlist, ALIGN=vehlist, COHESION=vehlist[1:])
        sheep.steering.set_target(EVADE=dog)
        sheep.steering.set_target(WANDER=(250, 10, 3))

    FREQ = 1200
    ticks = 0
    align_on = True
    while 1:
        ticks = ticks + 1
        
        if align_on and ticks > FREQ/2:
            align_on = False
            for sheep in vehlist[1:]:
                sheep.steering.pause('ALIGN')
                sheep.steering.pause('COHESION')
                
        if ticks > FREQ:
            ticks = 0
            align_on = True
            for sheep in vehlist[1:]:
                sheep.steering.resume('ALIGN')
                sheep.steering.resume('COHESION')
                
        for event in pygame.event.get():
            if event.type in [QUIT, MOUSEBUTTONDOWN]:
                pygame.quit()
                sys.exit()

        # Update Vehicles (via manually calling each move() method)
        for v in vehlist:
            v.move(UPDATE_SPEED)

        # Update Sprites (via pygame sprite group update)
        allsprites.update(UPDATE_SPEED)

        # Render
        screen.fill(bgcolor)
        allsprites.draw(screen)
        pygame.display.flip()
        
        #pygame.time.delay(2)

    # Clean-up here
    pygame.time.delay(2000)
