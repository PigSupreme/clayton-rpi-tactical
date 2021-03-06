#!/usr/bin/env python
"""Path-following vehicle demo."""

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
from steering import WaypointPath
ZERO_VECTOR = Point2d(0,0)

if __name__ == "__main__":
    pygame.init()

    # Display constants
    size = sc_width, sc_height = 800, 640
    screen = pygame.display.set_mode(size)
    pygame.display.set_caption('WaypointPath TRAVERSE vs. RESUME demo')
    bgcolor = 111, 145, 192

    # Update Speed
    UPDATE_SPEED = 0.25

    # Number of vehicles and obstacles
    numveh = 3
    numobs = 12
    total = 2*numveh+numobs

    # Waypoint/path information
    pathlen = 6
    min_dist_sq = 80**2

    # Sprite images and pygame rectangles
    img = list(range(total))
    rec = list(range(total))

    # Load vehicle images
    img[0], rec[0] = load_pygame_image('../images/gpig.png', -1)
    img[1], rec[1] = load_pygame_image('../images/ypig.png', -1)
    img[2], rec[2] = load_pygame_image('../images/rpig.png', -1)

    # Steering behaviour target images (generated here)
    for i in range(numveh, 2*numveh):
        img[i] = pygame.Surface((5,5))
        rec[i] = img[i].get_rect()

    # Static obstacle image (shared among all obstacles)
    obs_img, obs_rec = load_pygame_image('../images/circle.png', -1)
    for i in range(2*numveh, 2*numveh + numobs):
        img[i], rec[i] = obs_img, obs_rec

    # Randomly generate initial placement for vehicles
    pos = [Point2d(randint(30, sc_width-30), randint(30, sc_height-30)) for i in range(numveh)]
    #pos = [spos for i in range(numveh)]
    vel = Point2d(20,0)

    # Array of vehicles and associated pygame sprites
    obj = [SimpleVehicle2d(pos[i], 50, vel, (img[i], rec[i])) for i in range(numveh)]
    rgroup = [veh.sprite for veh in obj]
    vehicles = obj[:]

    # Steering behaviour targets (implemented as vehicles for later use...)
    for i in range(numveh, 2*numveh):
        new_pos = Point2d(5,5)
        target = SimpleVehicle2d(new_pos, 10, ZERO_VECTOR, (img[i], rec[i]))
        obj.append(target)
        rgroup.append(target.sprite)
    # List of targets for easy update
    targets = obj[numveh:2*numveh]

    # Static obstacles for pygame (randomly-generated positions)
    yoffset = sc_height//(numobs+1)
    yvals = list(range(yoffset, sc_height-yoffset, yoffset))
    shuffle(yvals)
    for i in range(2*numveh, 2*numveh + numobs):
        offset = (i+1.0-2*numveh)/(numobs+1)
        rany = yvals[i-2*numveh]
        new_pos = Point2d(offset*sc_width, rany)
        obstacle = SimpleObstacle2d(new_pos, 10, (img[i], rec[i]))
        obj.append(obstacle)
        rgroup.append(obstacle.sprite)
    # This gives a convenient list of (non-wall) obstacles for later use
    obslist = obj[2*numveh:]

    # Static Walls for pygame (screen border only)
    wall_list = (BaseWall2d((sc_width//2, 10), sc_width-20, 4, Point2d(0,1)),
                 BaseWall2d((sc_width//2, sc_height-10), sc_width-20, 4, Point2d(0,-1)),
                 BaseWall2d((10, sc_height//2), sc_height-20, 4, Point2d(1,0)),
                 BaseWall2d((sc_width-10,sc_height//2), sc_height-20, 4, Point2d(-1,0)))
    obj.extend(wall_list)
    for wall in wall_list:
        rgroup.append(wall.sprite)

    # Set-up pygame rendering
    allsprites = pygame.sprite.RenderPlain(rgroup)

    ### Vehicle steering behavior defined below ###
    # Randomly-generated list of waypoints for all vehicles
    #startp = (obj[0].pos.x, obj[0].pos.y)
    waylist = []
    while len(waylist) <= pathlen:
        newp = (randint(30, sc_width-30), randint(30, sc_height-30))
        newp2d = Point2d(*newp)
        d_min_sq = min([(obs.pos - newp2d).sqnorm() for obs in obslist])
        if d_min_sq > min_dist_sq:
            waylist.append(newp)
    waylist.append(obj[0].pos.ntuple())

    # Green (WAYPATHTRAVERSE)
    glist = [obj[0].pos.ntuple()] + waylist
    gpath = WaypointPath([Point2d(*p) for p in glist],True)
    obj[0].steering.set_target(WAYPATHTRAVERSE=gpath)
    obj[0].waypoint = obj[0].pos

    # Yellow (PATHRESUME)
    ylist = [obj[1].pos.ntuple()] + waylist
    ypath = WaypointPath([Point2d(*p) for p in ylist],True)
    obj[1].steering.set_target(WAYPATHRESUME=[ypath])
    obj[1].waypoint = obj[1].pos

    # Red (PATHRESUME, end after second cycle)
    rlist = [obj[2].pos.ntuple()] + 2*waylist
    rpath = WaypointPath([Point2d(*p) for p in rlist],False)
    obj[2].steering.set_target(WAYPATHRESUME=[rpath,0.05])
    obj[2].waypoint = obj[2].pos

    # All vehicles will avoid obstacles and walls
    for i in range(numveh):
        obj[i].steering.set_target(AVOID=obslist, WALLAVOID=[30, wall_list])
    ### End of vehicle behavior ###


    ### Main loop ###
    ticks = 0
    while 1:
        for event in pygame.event.get():
            if event.type in [QUIT, MOUSEBUTTONDOWN]:
                pygame.quit()
                sys.exit()

        # Update Vehicles (via manually calling each move() method)
        for veh in vehicles:
            veh.move(UPDATE_SPEED)

        # Update Sprites (via pygame sprite group update)
        allsprites.update(UPDATE_SPEED)

        #pygame.time.delay(10)

        # Screen update
        screen.fill(bgcolor)
        pygame.draw.lines(screen, (55,55,55), True, waylist, 2)
        allsprites.draw(screen)
        pygame.display.flip()

    pygame.time.delay(2000)
