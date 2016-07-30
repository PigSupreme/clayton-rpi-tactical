#!/usr/bin/env python
"""Non-flocking vehicle demo."""

# for python3 compat
from __future__ import unicode_literals
from __future__ import absolute_import
from __future__ import print_function
from __future__ import division

import sys, pygame
from pygame.locals import QUIT, MOUSEBUTTONDOWN
from random import randint, shuffle

INF = float('inf')
TARGET_FREQ = 1000

# Note: Adjust this depending on where this file ends up.
sys.path.append('..')
from vpoints.point2d import Point2d

from vehicle.vehicle2d import load_pygame_image
from vehicle.vehicle2d import SimpleVehicle2d, SimpleObstacle2d, BaseWall2d

import steering
steering.FLOCKING_RADIUS_MULTIPLIER = 1.2

UPDATE_SPEED = 0.2

if __name__ == "__main__":
    pygame.init()

    # Display constants
    size = sc_width, sc_height = 800, 640
    screen = pygame.display.set_mode(size)
    pygame.display.set_caption('FOLLOW (offset pursuit) demo')
    bgcolor = 111, 145, 192

    # Sprite images and pygame rectangles
    numveh = 6
    numobs = 12

    total = numveh+numobs
    img = list(range(total))
    rec = list(range(total))
    img[0], rec[0] = load_pygame_image('../images/gpig.png', -1)
    for i in range(1,numveh):
        img[i], rec[i] = load_pygame_image('../images/ypig.png', -1)

    # Static obstacles
    for i in range(numveh, numveh + numobs):
        img[i], rec[i] = load_pygame_image('../images/circle.png', -1)

    # Object physics for vehicles
    pos = [Point2d(randint(30, sc_width-30), randint(30, sc_height-30)) for i in range(numveh)]
    pos[0] = Point2d(sc_width/2, sc_height/2)
    vel = Point2d(20,0)

    # Array of vehicles for pygame
    obj = [SimpleVehicle2d(pos[i], 50, vel, (img[i], rec[i])) for i in range(numveh)]
    rgroup = [veh.sprite for veh in obj]
    
    # List of vehicles only, for later use
    vehlist = obj[:]

    # Static obstacles for pygame (randomly-generated positions)
    yoffset = sc_height//(numobs+1)
    yvals = list(range(yoffset, sc_height-yoffset, yoffset))
    shuffle(yvals)
    for i in range(numveh, numveh + numobs):
        offset = (i+1.0-numveh)/(numobs+1)
        rany = yvals[i-numveh]
        pos.append(Point2d(offset*sc_width, rany))
        obstacle = SimpleObstacle2d(pos[i], 10, (img[i], rec[i]))
        obj.append(obstacle)
        rgroup.append(obstacle.sprite)
    # This gives a convenient list of obstacles for later use
    obslist = obj[numveh:]

    # Static Walls: Only near screen boundary
    wall_list = (BaseWall2d((sc_width//2, 10), sc_width-20, 4, Point2d(0,1)),
                 BaseWall2d((sc_width//2, sc_height-10), sc_width-20, 4, Point2d(0,-1)),
                 BaseWall2d((10, sc_height//2), sc_height-20, 4, Point2d(1,0)),
                 BaseWall2d((sc_width-10,sc_height//2), sc_height-20, 4, Point2d(-1,0)))
    obj.extend(wall_list)
    rgroup.extend([wall.sprite for wall in wall_list])

    # Set-up pygame rendering
    allsprites = pygame.sprite.RenderPlain(rgroup)

    ### Vehicle behavior defined below ###
    # Green leader (WANDER)
    #obj[0].steering.set_target(WANDER=(40,30,5))
    #obj[0].maxspeed =2.0
    obj[0].steering.set_target(ARRIVE=(100,100))
    
    # Yellow (some kind of flocking)
    for i in range(1,numveh):
        #obj[i].steering.set_target(ALIGN=[obj[0]])
        #obj[i].steering.set_target(SEPARATE=[obj[i] for i in range(numveh)])
        pass

    # Formation    
    obj[1].steering.set_target(FOLLOW=(obj[0], Point2d(-40,20)))
    obj[2].steering.set_target(FOLLOW=(obj[0], Point2d(-40,-20)))
    obj[3].steering.set_target(FOLLOW=(obj[0], Point2d(-80,40)))
    obj[4].steering.set_target(FOLLOW=(obj[0], Point2d(-80,0)))
    obj[5].steering.set_target(FOLLOW=(obj[0], Point2d(-80,-40)))

    # All vehicles will avoid obstacles and walls
    for i in range(numveh):
        obj[i].steering.set_target(AVOID=obslist, WALLAVOID=[30, wall_list])

    ### End of vehicle behavior ###

    ticks = 0
    while 1:
        for event in pygame.event.get():
            if event.type in [QUIT, MOUSEBUTTONDOWN]:
                pygame.quit()
                sys.exit()
                
        # Update leader's target every so often
        ticks += 1
        if ticks == TARGET_FREQ:
            # Green target
            x_new = randint(30, sc_width-30)
            y_new = randint(30, sc_height-30)
            new_pos = Point2d(x_new,y_new)
            obj[0].steering.set_target(ARRIVE=(x_new,y_new))
            ticks = 0

        # Update Vehicles (via manually calling each move() method)
        for v in vehlist:
            v.move(UPDATE_SPEED)

        # Update Sprites (via pygame sprite group update)
        allsprites.update(UPDATE_SPEED)

        # Render
        screen.fill(bgcolor)
        allsprites.draw(screen)
        pygame.display.flip()

    pygame.time.delay(2000)
