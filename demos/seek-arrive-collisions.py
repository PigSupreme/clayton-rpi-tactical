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

TARGET_FREQ = 500

INF = float('inf')

# Note: Adjust this depending on where this file ends up.
sys.path.append('..')
from vpoints.point2d import Point2d

from vehicle.vehicle2d import load_pygame_image
from vehicle.vehicle2d import SimpleVehicle2d, SimpleObstacle2d, BaseWall2d
ZERO_VECTOR = Point2d(0,0)

if __name__ == "__main__":
    pygame.init()

    # Display constants
    size = sc_width, sc_height = 800, 640
    screen = pygame.display.set_mode(size)
    pygame.display.set_caption('SEEK - ARRIVE demo with Pygame collisions')
    bgcolor = 111, 145, 192

    # Update Speed
    UPDATE_SPEED = 0.2

    # Number of vehicles and obstacles
    numveh = 3
    numobs = 16
    total = 2*numveh+numobs

    # Sprite images and pygame rectangles
    img = list(range(total))
    rec = list(range(total))

    # Load vehicle images
    img[0], rec[0] = load_pygame_image('../images/rpig.png', -1)
    img[1], rec[1] = load_pygame_image('../images/ypig.png', -1)
    img[2], rec[2] = load_pygame_image('../images/gpig.png', -1)

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
    pos[0] = Point2d(sc_width/2, sc_height/2)
    vel = Point2d(20,0)

    # Array of vehicles and associated pygame sprites
    obj = list(range(numveh))
    for i in range(numveh):
        obj[i] = SimpleVehicle2d(pos[i], 50, vel, (img[i], rec[i]))
        obj[i].ent_id = i
    rgroup = [veh.sprite for veh in obj]
    vehicles = obj[:]

    # Steering behaviour targets (implemented as vehicles for later use...)
    for i in range(numveh, 2*numveh):
        x_new = randint(30, sc_width-30)
        y_new = randint(30, sc_height-30)
        new_pos = Point2d(x_new,y_new)
        target = SimpleVehicle2d(new_pos, 10, ZERO_VECTOR, (img[i], rec[i]))
        obj.append(target)
        rgroup.append(target.sprite)

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
    # Big red (ARRIVE, medium hesitance)
    x_new, y_new = obj[3].pos[0], obj[3].pos[1]
    obj[0].steering.set_target(ARRIVE=(x_new,y_new,3.0))

    # Yellow (ARRIVE, low hesitance)
    x_new, y_new = obj[4].pos[0], obj[4].pos[1]
    obj[1].steering.set_target(ARRIVE=(x_new,y_new,0.5))

    # Green (SEEK)
    x_new, y_new = obj[5].pos[0], obj[5].pos[1]
    obj[2].steering.set_target(SEEK=(x_new, y_new))

    # Target sprite groups for each vehicle
    for i in range(numveh):
        obj[i].tgroup = pygame.sprite.GroupSingle(obj[i + numveh].sprite)

    # All vehicles will avoid obstacles and walls
    for i in range(3):
        obj[i].steering.set_target(AVOID=obslist, WALLAVOID=[30, wall_list])
    ### End of vehicle behavior ###

    # Used by pygame for collision detection
    COLLIDE_FUNCTION = pygame.sprite.collide_circle

    ### Main loop ###
    ticks = 0
    while 1:
        for event in pygame.event.get():
            if event.type in [QUIT, MOUSEBUTTONDOWN]:
                pygame.quit()
                sys.exit()

        # Update Vehicles (via manually calling each move() method)
        for v in vehicles:
            v_id = v.ent_id
            v.move(UPDATE_SPEED)
            hit_list = pygame.sprite.spritecollide(v.sprite, v.tgroup, False, COLLIDE_FUNCTION)
            if len(hit_list) > 0:
                print("Vehicle %d: Now at target!" % v_id)
                v.tgroup.remove(obj[v_id + numveh].sprite)

        # Update steering targets every so often
        ticks += 1
        if ticks == TARGET_FREQ:
            # Green target
            x_new = randint(30, sc_width-30)
            y_new = randint(30, sc_height-30)
            new_pos = Point2d(x_new,y_new)
            obj[5].pos = new_pos
            obj[2].steering.set_target(SEEK=(x_new,y_new))
            obj[2].tgroup.add(obj[5].sprite)

        if ticks == TARGET_FREQ*2:
            # Yellow target
            x_new = randint(30, sc_width-30)
            y_new = randint(30, sc_height-30)
            new_pos = Point2d(x_new,y_new)
            obj[4].pos = new_pos
            obj[1].steering.set_target(ARRIVE=(x_new,y_new,0.5))
            obj[1].tgroup.add(obj[4].sprite)

        if ticks == TARGET_FREQ*3:
            # Red target
            x_new = randint(30, sc_width-30)
            y_new = randint(30, sc_height-30)
            new_pos = Point2d(x_new,y_new)
            obj[3].pos = new_pos
            obj[0].steering.set_target(ARRIVE=(x_new,y_new,3.0))
            obj[0].tgroup.add(obj[3].sprite)
            ticks = 0

        # Update Sprites (via pygame sprite group update)
        allsprites.update(UPDATE_SPEED)

        #pygame.time.delay(2)

        # Screen update; inefficient!
        screen.fill(bgcolor)
        allsprites.draw(screen)
        pygame.display.flip()

    pygame.time.delay(2000)
