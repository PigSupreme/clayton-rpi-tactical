#!/usr/bin/env python
"""Non-flocking vehicle demo."""

# for python3 compat
from __future__ import unicode_literals
from __future__ import absolute_import
from __future__ import print_function

import os, sys, pygame
from pygame.locals import RLEACCEL, QUIT, MOUSEBUTTONDOWN
from random import randint, shuffle

TARGET_FREQ = 500

INF = float('inf')

# Note: Adjust this depending on where this file ends up.
sys.path.insert(0, '../vpoints')
from point2d import Point2d

def load_image(name, colorkey=None):
    """Loads image from current working directory for use in pygame.

    Parameters
    ----------
    name: string
        Image file to load (must be pygame-compatible format)
    colorkey: pygame.Color
        Used to set a background color for this image that will be ignored
        during blitting. If set to -1, the upper-left pixel color will be
        used as the background color. See pygame.Surface.set_colorkey() for
        further details.

    Returns
    -------
    (pygame.Surface, pygame.rect):
        For performance reasons, the returned Surface is the same format as
        the pygame display. The alpha channel is removed.

    """
    imagefile = os.path.join(os.getcwd(), name)
    try:
        image_surf = pygame.image.load(imagefile)
    except pygame.error, message:
        print('Error: Cannot load image: %s' % name)
        raise SystemExit(message)

    # This converts the surface for maximum blitting performance,
    # including removal of any alpha channel:
    image_surf = image_surf.convert()

    # This sets the background (ignored during blit) color:
    if colorkey is not None:
        if colorkey is -1:
            colorkey = image_surf.get_at((0,0))
        image_surf.set_colorkey(colorkey, RLEACCEL)
    return image_surf, image_surf.get_rect()


if __name__ == "__main__":
    from vehicle2d import PointMass2d, StaticMass2d, SimpleWall2d


    pygame.init()

    # Display constants
    size = sc_width, sc_height = 800, 640
    screen = pygame.display.set_mode(size)
    bgcolor = 111, 145, 192

    # Sprite images and pygame rectangles
    numveh = 3
    numobs = 16

    total = 2*numveh+numobs
    img = list(range(total))
    rec = list(range(total))
    img[0], rec[0] = load_image('rpig.png', -1)
    img[1], rec[1] = load_image('ypig.png', -1)
    img[2], rec[2] = load_image('gpig.png', -1)

    # Steering behaviour targets 
    for i in range(numveh, 2*numveh):
        img[i] = pygame.Surface((5,5))
        rec[i] = img[i].get_rect()
    numveh *= 2

    # Static obstacles
    for i in range(numveh, numveh + numobs):
        img[i], rec[i] = load_image('circle.png', -1)

    StaticMass2d.tagged_image = load_image('circle_tag.png', -1)[0]

    # Object physics for vehicles
    pos = [Point2d(randint(30, sc_width-30), randint(30, sc_height-30)) for i in range(numveh)]
    pos[0] = Point2d(sc_width/2, sc_height/2)
    vel = Point2d(20,0)

    # Array of vehicles for pygame
    obj = [PointMass2d(img[i], rec[i], pos[i], 50, vel) for i in range(numveh//2)]

    # Steering behaviour target sprites 
    for i in range(numveh//2, numveh):
        img[i] = pygame.Surface((5,5))
        rec[i] = img[i].get_rect()
        pos.append(Point2d(0,0))
        obj.append(StaticMass2d(img[i], rec[i], pos[i], 10, vel))

    # Static obstacles for pygame (randomly-generated positions)
    yoffset = sc_height/(numobs+1)
    yvals = list(range(yoffset, sc_height-yoffset, yoffset))
    shuffle(yvals)
    for i in range(numveh, numveh + numobs):
        offset = (i+1.0-numveh)/(numobs+1)
        rany = yvals[i-numveh]
        pos.append(Point2d(offset*sc_width, rany))
        obj.append(StaticMass2d(img[i], rec[i], pos[i], 10, vel))
    # This gives a convenient list of obstacles for later use
    obslist = obj[numveh:]

    # Static Walls for pygame (screen border only)
    wall_list = (SimpleWall2d((sc_width//2, 10), sc_width-20, 4, Point2d(0,1)),
                 SimpleWall2d((sc_width//2, sc_height-10), sc_width-20, 4, Point2d(0,-1)),
                 SimpleWall2d((10, sc_height//2), sc_height-20, 4, Point2d(1,0)),
                 SimpleWall2d((sc_width-10,sc_height//2), sc_height-20, 4, Point2d(-1,0)))
    obj.extend(wall_list)

    # Set-up pygame rendering
    allsprites = pygame.sprite.RenderPlain(obj)

    ### Vehicle behavior defined below ###
    # Big red (WANDER)
    obj[0].steering.set_target(ARRIVE=obj[3].rect.center)
    
    # Yellow (ARRIVE)
    obj[1].steering.set_target(ARRIVE=obj[4].rect.center)

    # Green (SEEK)
    obj[2].steering.set_target(SEEK=obj[5].rect.center)

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

        # Update steering targets every so often
        ticks += 1
        if ticks == TARGET_FREQ:
            # Green target
            x_new = randint(30, sc_width-30)
            y_new = randint(30, sc_height-30)
            new_pos = Point2d(x_new,y_new)
            obj[5].rect.center = (x_new, y_new)
            obj[2].steering.set_target(SEEK=(x_new,y_new))

        if ticks == TARGET_FREQ*2:
            # Yellow target
            x_new = randint(30, sc_width-30)
            y_new = randint(30, sc_height-30)
            new_pos = Point2d(x_new,y_new)
            obj[4].rect.center = (x_new, y_new)
            obj[1].steering.set_target(ARRIVE=(x_new,y_new,1.0))

        if ticks == TARGET_FREQ*3:
            # Red target
            x_new = randint(30, sc_width-30)
            y_new = randint(30, sc_height-30)
            new_pos = Point2d(x_new,y_new)
            obj[3].rect.center = (x_new, y_new)
            obj[0].steering.set_target(ARRIVE=(x_new,y_new,3.0))
            ticks = 0

        # Mother Nature will be like, sloooooow dowwwwwwn....
        allsprites.update(0.2)

        #pygame.time.delay(2)

        # Render
        screen.fill(bgcolor)
        allsprites.draw(screen)

        # Draw the force vectors for each vehicle
#        for i in range(numveh):
#            vehicle = obj[i]
#            g_pos = vehicle.pos
#            g_force = g_pos + vehicle.force.scale(25)
#            pygame.draw.line(screen, (0,0,0), g_pos.ntuple(), g_force.ntuple(), 3)

        pygame.display.flip()

    pygame.time.delay(2000)
