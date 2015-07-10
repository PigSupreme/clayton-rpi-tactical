#!/usr/bin/python

import os, sys, pygame, random
from pygame.locals import *
from math import sqrt, atan, degrees
random.seed()
randint = random.randint

def normalize(vec):
    """Returns a unit vector in the direction of (x,y)"""
    x,y = vec
    norm = sqrt(x*x+y*y)
    return [x/norm,y/norm]

def angle_from_vector(vec):
    """Returns the polar angle in degrees to the given vector""" 
    x,y = vec
    try:
        theta = degrees(atan(y/x))
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
    def __init__(self,image,rect,position,radius,facing):
        # Must call pygame's Sprite.__init__ first!
        pygame.sprite.Sprite.__init__(self)
        self.orig = image
        self.image = image
        self.rect = rect        
        
        # Basic object physics
        self.pos = position    # Center of object
        self.radius = radius   # Bounding radius
        self.vel = [randint(-17,17),randint(-6,6)]       # Current Velocity
        
        # Normalized front/left vector in world coordinates
        self.front = normalize(facing)
        self.left = (-self.front[1],self.front[0])
        
        # Angle of facing (degrees, polar coordinates)   
        self.theta = angle_from_vector(self.front)
        
        # Rotational velocity (degrees per time)
        self.omega = randint(-15,15)    
        
        # Movement constraints
        self.mass = 1
        self.maxspeed = 10
        self.maxforce = 100
        self.maxrotation = 60
    
    def move(self,delta_t):
        # Simple edge-warping behaviour
        x = (self.pos[0] + delta_t*self.vel[0]) #% sc_width
        y = (self.pos[1] + delta_t*self.vel[1]) #% sc_height
        self.pos = (x,y)
        self.rect.center = self.pos[0],self.pos[1]
        
    def rotate(self,delta_t):
        # Rotation about image center
        self.theta = (self.theta + self.omega*delta_t) % 360
        center = self.rect.center
        self.image = pygame.transform.rotate(self.orig,self.theta)
        self.rect = self.image.get_rect()
        self.rect.center = center
        
    def update(self,dt=1.0):
        self.move(dt)
        if self.rect.left < 0 or self.rect.right > sc_width:
            self.vel[0] = -self.vel[0]
            self.omega = -self.omega
        if self.rect.top < 0 or self.rect.bottom > sc_height:
            self.vel[1] = -self.vel[1]
            self.omega = -self.omega
        self.rotate(dt)     
        

        

pygame.init()

# Display constants
size = sc_width, sc_height = 960, 800
screen = pygame.display.set_mode(size)

bgcolor = 111, 145, 192

img, rec = load_image('pig.png',-1)
angle = 0
x, y = sc_width/2, sc_height/2

# Create some objects
n = 28
obj = [MovingObject(img,rec,(x,y),20,(1,2)) for i in range(n)]
allsprites = pygame.sprite.RenderPlain(obj)

while 1:
    for event in pygame.event.get():
        if event.type in [QUIT,MOUSEBUTTONDOWN]:
            pygame.quit()
            sys.exit()

    allsprites.update(1.0)

    pygame.time.delay(50)    

    # Render
    screen.fill(bgcolor)
    allsprites.draw(screen)
    pygame.display.flip()


pygame.time.delay(2000)