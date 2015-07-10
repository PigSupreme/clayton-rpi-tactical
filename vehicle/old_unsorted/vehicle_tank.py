#!/usr/bin/python
"""Tank-style controls using pygame joystick interface.
Need to import Point2d from the correct place; vectest.py no longer
exists.
"""


import os, sys, pygame, random
from pygame.locals import *
from math import sqrt, atan, degrees
random.seed()
randint = random.randint

from vectest import Point2d, unit_dir

def normalize(vec):
    """Returns a unit vector in the direction of (x,y)"""
    x,y = vec
    norm = sqrt(x*x+y*y)
    try:
        return [x/norm,y/norm]
    except ZeroDivisionError:
        return [0,0]

def angle_from_vector(vec):
    """Returns the polar angle in degrees to the given vector""" 
    x,y = vec[0], vec[1]
    try:
        theta = degrees(atan(-y/x))
        if x<0:
            theta = (theta + 180)
    except ZeroDivisionError:
        if y>0:
            theta = 90
        elif y<0:
            theta = -90
        else:
            raise ValueError
    return theta

def load_image(name,colorkey=None):
    """Loads image from current directory\n
    returns Surface, rect"""
    imagefile = os.path.join(os.getcwd(),name)
    try:
        image = pygame.image.load(imagefile)
    except pygame.error, message:
        print 'Error: Cannot load image:', name
        raise SystemExit, message
    image = image.convert()
    if colorkey is not None:
        if colorkey is -1:
            colorkey=image.get_at((0,0))
        image.set_colorkey(colorkey,RLEACCEL)
    return image, image.get_rect()

class MovingObject(pygame.sprite.Sprite):
    """pygame Sprite + fine motor control"""
    def __init__(self,image,rect,position,radius,velocity):
        # Must call pygame's Sprite.__init__ first!
        pygame.sprite.Sprite.__init__(self)
        self.orig = image
        self.image = image
        self.rect = rect        
        
        # Basic object physics
        self.pos = position    # Center of object: Point2d
        self.radius = radius   # Bounding radius
        self.vel = velocity       # Current Velocity: Point2d
        
        # Normalized front/left vector in world coordinates
        self.front = Point2d(1,0)
        self.left = Point2d(-self.front[1],self.front[0])
        
        # Angle of facing (degrees, polar coordinates)   
        self.theta = self.front.angle()
        
        # Rotational velocity (degrees per time)
        self.omega = 0   
        
        # Movement constraints
        self.mass = 1
        self.maxspeed = 15
        self.maxforce = 100
        #self.maxrotation = 60
    
    def move(self,delta_t):
        self.pos = self.pos + self.vel.scale(delta_t)
        self.rect.center = self.pos[0],self.pos[1]
        
        
    def rotate(self,delta_t):
        # Rotation about image center
        self.theta = self.theta + self.omega*delta_t
        center = self.rect.center
        self.image = pygame.transform.rotate(self.orig,self.theta*180/3.141592654)
        self.rect = self.image.get_rect()
        self.rect.center = center
        # Next angle is negative to work with screen coordinates
        self.front = unit_dir(-self.theta)        

        # set self.left here
        
    def update(self,dt=1.0,tank_l=0.0,tank_r=0.0):
                        
        # Update velocity and heading
        vr = tank_l
        vl = tank_r
        rad = 64.0
        
        # Align velocity with heading:
        # self.front is already a unit vector
        self.vel = self.front.scale(vr+vl)        
        #self.vel = self.vel + accel
        self.vel.truncate(self.maxspeed)
        
        # Angular velocity, based on difference in side vel's
        # This is backwards to work with screen coordinates
        self.omega = (vr-vl)/rad
                 
        # Movement here
        self.move(dt)
        self.rotate(dt)
        
        # Simple edge warp
        if False:
            self.rect.left = self.rect.left % sc_width
            self.rect.top = self.rec.top % sc_height

        

pygame.init()
pygame.joystick.init()
joystick = pygame.joystick.Joystick(0)
joystick.init()

# Display constants
size = sc_width, sc_height = 960, 800
screen = pygame.display.set_mode(size)

bgcolor = 111, 145, 192

img, rec = load_image('tank.png',-1)
angle = 0
pos = Point2d(sc_width/2, sc_height/2)
vel = Point2d(-60,4)

# Create some objects
n = 1
obj = [MovingObject(img,rec,pos,20,vel) for i in range(n)]

allsprites = pygame.sprite.RenderPlain(obj)

while 1:
    for event in pygame.event.get():
        if event.type in [QUIT,MOUSEBUTTONDOWN]:
            pygame.quit()
            sys.exit()
    
    # Triangle to quit
    if joystick.get_button(3) == 1:
        pygame.quit()
        sys.exit()
        
    # X to reset tank position
    if joystick.get_button(1) == 1:
        obj[0].pos = Point2d(sc_width/2,sc_height/2)
        obj[0].theta = 0

    stick_l = -joystick.get_axis(1)*6
    stick_r = -joystick.get_axis(3)*6

    allsprites.update(1.0,stick_l,stick_r)

    

    theta = obj[0].theta
    front = obj[0].front
    pygame.time.delay(50)    

    # Render
    screen.fill(bgcolor)
    allsprites.draw(screen)
    pygame.display.flip()


pygame.time.delay(2000)