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

# Note: Adjust this depending on where this file ends up.
sys.path.append('..')
from vpoints.point2d import Point2d

from vehicle.vehicle2d import load_pygame_image
from vehicle.vehicle2d import SimpleVehicle2d, SimpleObstacle2d, BaseWall2d

UPDATE_SPEED = 0.5

if __name__ == "__main__":
    pygame.init()

    # Display constants
    size = sc_width, sc_height = 1080, 960
    screen = pygame.display.set_mode(size)
    pygame.display.set_caption('Guard/Stalking demo')
    bgcolor = 111, 145, 192

    # Sprite images and pygame rectangles
    numveh = 10
    numobs = 25

    img = list(range(numveh+numobs))
    rec = list(range(numveh+numobs))
    img[0], rec[0] = load_pygame_image('../images/rpig.png', -1)
    for i in range(1, 2):
        img[i], rec[i] = load_pygame_image('../images/ypig.png', -1)
    for i in range(2, numveh):
        img[i], rec[i] = load_pygame_image('../images/gpig.png', -1)

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

    # Static obstacles for pygame
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

    # Set-up pygame rendering for all objects
    allsprites = pygame.sprite.RenderPlain(rgroup)

    ### Vehicle behavior defined below ###

    # Big red arrow: Wander and Avoid obstacles, SEPARATE from Yellow
    obj[0].maxspeed = 4.0
    obj[0].steering.set_target(WANDER=(250, 50, 10))
    obj[0].radius = 100
    obj[0].steering.set_target(SEPARATE=[obj[1]])

    #Old examples, updated for new syntax
    #obj[1].steering.set_target(SEEK=(500,300))
    #obj[1].steering.set_target(FLEE=(500,400))

    # Yellow arrow: Guard RED from GREEN leader, SEPARATE from RED
    obj[1].maxspeed = 5.0
    obj[1].steering.set_target(GUARD=(obj[0], obj[2], 0.25))
    obj[1].steering.set_target(SEPARATE=[obj[0]])

    # Green arrows; TAKECOVER from YELLOW, WANDER, and SEPRATE each other
    for i in range(2, numveh):
        obj[i].maxspeed = 3.0
        obj[i].steering.set_target(PURSUE=obj[0], TAKECOVER=(obj[1], obslist, 120, True))
#        obj[i].steering.set_target(WANDER=(60,10,3))
        obj[i].steering.set_target(SEPARATE=[obj[j] for j in range(2, numveh)])
#        obj[i].steering.set_target(ALIGN=[obj[j] for j in range(2, numveh)])
#        obj[i].steering.set_target(COHESION=[obj[j] for j in range(2, numveh)])
    # This was old demo:
    #obj[2].steering.set_target(PURSUE=obj[0], EVADE=obj[1])

    # Green arrow followers: Follow GREEN leader and evade YELLOW
    #obj[3].maxspeed = 3.0
    #obj[3].steering.set_target(FOLLOW=(obj[2], Point2d(-30,30)), EVADE=obj[1])
    #obj[4].maxspeed = 3.0
    #obj[4].steering.set_target(FOLLOW=(obj[2], Point2d(-30,-30)), EVADE=obj[1])

    # All vehicles will avoid obstacles and walls
    for i in range(numveh):
        obj[i].steering.set_target(AVOID=obslist, WALLAVOID=[50, wall_list])

    ### End of vehicle behavior ###

    while 1:
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

    pygame.time.delay(2000)
