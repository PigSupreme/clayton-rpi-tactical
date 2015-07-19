#!/usr/bin/env python
"""Simple pygame demo showing seek/flee steering behavior.

The red boid seeks to randomly-generated point, ignoring other boids. Once it
gets close enough to this target point, a new one is generated.

Yellow boids follow the same behavior, but also flee from the red boid if it
gets too close. The jittering will be dealt with later.
"""

# for python3 compat
from __future__ import unicode_literals
from __future__ import absolute_import
from __future__ import print_function

import os, sys, pygame
from pygame.locals import *

from random import seed, randint
INF = float('inf')

sys.path.insert(0,'../vpoints')
from point2d import Point2d

# Point2d functions return radians, but pygame wants degrees. The negative
# is needed since y coordinates increase downwards on screen. Multiply a
# math radians result by DEG to get pygame screen-appropriate degrees.
DEG = -57.2957795131

#random seed
seed()


def load_image(name, colorkey=None):
    """Loads image from current working directory for use in pygame.

    Parameters
    ----------
    name: string
        Image file to load (must be pygame-compatible format)
    colorkey: pygame.Color
        Used to set a background color for this image that will be ignored
        during blitting. If set to -1, the upper-left pixel color will be
        used as the background color. See pygame.Surface.set_colorkey().

    Returns
    -------
    (Surface, rect):
        For performance reasons, the returned Surface is the same format as
        the pygame display. The alpha channel is removed.

    """
    imagefile = os.path.join(os.getcwd(),name)
    try:
        image_surf = pygame.image.load(imagefile)
    except pygame.error, message:
        print 'Error: Cannot load image:', name
        raise SystemExit, message

    # This converts the surface for maximum blitting performance,
    # including removal of any alpha channel:
    image_surf = image_surf.convert()

    # This sets the background (ignored during blit) color:
    if colorkey is not None:
        if colorkey is -1:
            colorkey=image_surf.get_at((0,0))
        image_surf.set_colorkey(colorkey,RLEACCEL)
    return image_surf, image_surf.get_rect()

class MovingObject(pygame.sprite.Sprite):
    """A pygame.Sprite with basic physics."""
    def __init__(self,image,rect,position,radius,velocity):
        # Must call pygame's Sprite.__init__ first!
        pygame.sprite.Sprite.__init__(self)

        # Pygame image information for blitting
        self.orig = image
        self.image = image
        self.rect = rect

        # Basic object physics
        self.pos = position    # Center of object: Point2d
        self.radius = radius   # Bounding radius
        self.vel = velocity    # Current Velocity: Point2d

        # Normalized front/left vector in world coordinates
        self.front = velocity.unit()
        self.left = Point2d(-self.front[1],self.front[0])

        # Seek target
        self.target = Point2d(randint(10,sc_width-10),randint(10,sc_height-10))

        # Angle of facing (degrees, polar coordinates)
        #self.theta = angle_from_vector(self.front)

        # Rotational velocity (degrees per time)
        #self.omega = randint(-15,15)

        # Movement constraints
        self.mass = 1
        self.maxspeed = 12
        self.maxforce = 1.5
        #self.maxrotation = 60

    def move(self,delta_t):
        """Update the position of this object, using its current velocity.

        Parameters
        ----------
        delta_t: float
            Time increment since last move.
        """
        self.pos = self.pos + self.vel.scale(delta_t)
        self.rect.center = self.pos[0],self.pos[1]

    def _rotate_for_blit(self,delta_t):
        """Used to rotate the object's image prior to blitting.

        Note
        ----
        This function does not update any physics, it only rotates the image,
        based on the object's current front vector.
        """
        theta = self.front.angle()*DEG
        center = self.rect.center
        self.image = pygame.transform.rotate(self.orig,theta)
        self.rect = self.image.get_rect()
        self.rect.center = center

    def update(self,dt=1.0):
        """Document this!!!"""
        # If we're within a certain distance of target, generate a new target
        # This should be done by the FSM code once that's integrated.
        if (self.pos - self.target).sqnorm() < 9:
            self.target = Point2d(randint(10,sc_width-10),randint(10,sc_height-10))
            #print('New target: %d, %d' % (self.target[0],self.target[1]))

        # Steering force calculated here (for now, demo seek/flee)
        # This should be done by SteeringBehaviors, once that's integrated.
        if self.flee:
            sforce = flee_force(self,obj[0].pos,25000) + arrive_force(self,self.target, 0.2)
        else:
            sforce = seek_force(self,self.target)
        # End of steering behavior

        # Don't exceed maximum possible force; then compute acceleration
        sforce.truncate(self.maxforce)
        accel = sforce.scale(1.0/self.mass)

        # Update velocity and heading; don't exceed maximum speed
        self.vel = self.vel + accel
        self.vel.truncate(self.maxspeed)

        # Align heading with velocity (unless velocity is very small)
        ##################
        # TODO: Don't exceed maximum angular speed
        ##################
        if self.vel.sqnorm() > .000000001:
            self.front = self.vel.unit()
            self.left = Point2d(-self.front[1],self.front[0])

        # Movement here
        self.move(dt)
        self._rotate_for_blit(dt)


def seek_force(obj,tpos):
    """ Returns the steering force for obj to seek position tpos.

    Note
    ----
    This should be moved into steering.py (DONE!)
    """
    targetvel = (tpos - obj.pos).unit()
    targetvel = targetvel.scale(obj.maxspeed)
    return targetvel - obj.vel

def flee_force(obj,tpos,dsq = INF):
    """ Returns the steering force for obj to flee from position tpos.

    Note
    ----
    This should be moved into steering.py (DONE!)
    """
    targetvel = obj.pos - tpos
    if 1 < targetvel.sqnorm() < dsq:
        targetvel = targetvel.unit().scale(obj.maxspeed)
        return targetvel - obj.vel
    else:
        return Point2d(0,0)

def arrive_force(obj,tpos,hesitance=2.0):
    """ Returns the steering force for obj to arrive at position tpos.

    Note
    ----
    This should be moved into steering.py
    """
    target_offset = (tpos - obj.pos)
    dist = target_offset.norm()
    if dist > 0:
        # The constant on the next line may need tweaking
        speed = dist / (10.0 * hesitance)
        if speed > obj.maxspeed:
            speed = obj.maxspeed    
        targetvel = target_offset.scale(speed/dist)
        return targetvel - obj.vel
    else:
        return Point2d(0,0)

if __name__ == "__main__":
    pygame.init()

    # Display constants
    size = sc_width, sc_height = 960, 800
    screen = pygame.display.set_mode(size)
    bgcolor = 111, 145, 192

    # Sprite images and pygame rectangles
    numobj = 52
    img=list(range(numobj))
    rec=list(range(numobj))
    img[0], rec[0] = load_image('rpig.png',-1)
    for i in range(1,numobj):
        img[i], rec[i] = load_image('ypig.png',-1)

    # Object physics
    angle = 0
    pos = [Point2d(i*sc_width/(1+numobj), i*sc_height/(1+numobj)) for i in range(1,1+numobj)]
    vel = Point2d(20,-20)

    # Create any array of objects for pygame
    obj = [MovingObject(img[i],rec[i],pos[i],20,vel) for i in range(numobj)]
    obj[0].flee = False
    obj[0].maxspeed = 5
    for i in range(1,numobj):
        obj[i].flee = True
    allsprites = pygame.sprite.RenderPlain(obj)

    while 1:
        for event in pygame.event.get():
            if event.type in [QUIT,MOUSEBUTTONDOWN]:
                pygame.quit()
                sys.exit()

        allsprites.update(0.1)

        #pygame.time.delay(5)

        # Render
        screen.fill(bgcolor)
        allsprites.draw(screen)
        pygame.display.flip()


    pygame.time.delay(2000)
