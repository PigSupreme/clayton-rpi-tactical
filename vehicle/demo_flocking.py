#!/usr/bin/env python
"""Flocking vehicle demo."""

# for python3 compat
from __future__ import unicode_literals
from __future__ import absolute_import
from __future__ import print_function
from __future__ import division

import os, sys, pygame
from pygame.locals import RLEACCEL, QUIT, MOUSEBUTTONDOWN
from random import randint, shuffle

# INF = float('inf')

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
    import steering
    steering.FLOCKING_RADIUS_MULTIPLIER = 3.0
    steering.EVADE_PANIC_SQ = 180**2

    pygame.init()

    # Display constants
    size = sc_width, sc_height = 1080, 960
    screen = pygame.display.set_mode(size)
    bgcolor = 111, 145, 192

    # Sprite images and pygame rectangles
    numveh = 30
    numobs = 15
    img = list(range(numveh+numobs))
    rec = list(range(numveh+numobs))

    # Vehicle Sprites
    img[0], rec[0] = load_image('ypig.png', -1)
    for i in range(1, numveh):
        img[i], rec[i] = load_image('gpig.png', -1)
    # Vehicle Physics
    pos = [Point2d(randint(30, sc_width-30), randint(30, sc_height-30)) for i in range(numveh)]
    pos[0] = Point2d(sc_width/2, sc_height/2)
    vel = Point2d(5.0,0).rotated_by(147*i, True)
    # List of vehicles (used later as a pygame Sprite group_)
    obj = [PointMass2d(img[i], rec[i], pos[i], 50, vel) for i in range(numveh)]
    # List of vehicles only, for later use
    vehlist = obj[:]


    # Static obstacle Sprites
    for i in range(numveh, numveh + numobs):
        img[i], rec[i] = load_image('circle.png', -1)
    StaticMass2d.tagged_image = load_image('circle_tag.png', -1)[0]
    # Static obstacle Physics
    yoffset = sc_height//(numobs+1)
    yvals = list(range(yoffset, sc_height-yoffset, yoffset))
    yvals.append(yoffset)
    shuffle(yvals)
    for i in range(numveh, numveh + numobs):
        print('i = %d, i-numveh = %d' % (i, i-numveh))
        offset = (i+1.0-numveh)/(numobs+1)
        rany = yvals[i-numveh]
        pos.append(Point2d(offset*sc_width, rany))
        obj.append(StaticMass2d(img[i], rec[i], pos[i], 10, vel))
    # List of obstacles only, for later use
    obslist = obj[numveh:]


    # Static Walls: Only near screen boundary
    # Commented walls below were for testing
    walllist = (SimpleWall2d((sc_width//2, 10), sc_width-20, 4, Point2d(0,1)),
                 SimpleWall2d((sc_width//2, sc_height-10), sc_width-20, 4, Point2d(0,-1)),
                 SimpleWall2d((10, sc_height//2), sc_height-20, 4, Point2d(1,0)),
                 SimpleWall2d((sc_width-10,sc_height//2), sc_height-20, 4, Point2d(-1,0)))
#                 SimpleWall2d((2+sc_width//2, 2+sc_height//2), min(sc_width,sc_height), 4, Point2d(1,1)),
#                 SimpleWall2d((sc_width//2, sc_height//2), min(sc_width,sc_height), 4, Point2d(-1,-1)),
#                 SimpleWall2d((sc_width//3, sc_height//2), sc_height//3, 4, Point2d(1,0)),
#                 SimpleWall2d((sc_width//3-2, sc_height//2), sc_height//3, 4, Point2d(-1,0))
#                 }
    obj.extend(walllist)

    # Set-up pygame rendering for all objects
    allsprites = pygame.sprite.RenderPlain(obj)

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

    while 1:
        for event in pygame.event.get():
            if event.type in [QUIT, MOUSEBUTTONDOWN]:
                pygame.quit()
                sys.exit()

        #for wall in walllist:
        #    wall.tagged = False

        allsprites.update(0.5)
        #pygame.time.delay(5)

        # Render
        screen.fill(bgcolor)
        allsprites.draw(screen)

        # Draw the force vectors for each vehicle
#        for i in range(numveh):
#            vehicle = obj[i]
#            g_pos = vehicle.pos
#            g_force = g_pos + vehicle.force.scale(5)
#            pygame.draw.line(screen, (0,0,0), g_pos.ntuple(), g_force.ntuple(), 3)

        pygame.display.flip()

    # Clean-up here
    pygame.time.delay(2000)
