#!/usr/bin/env python

# for python3 compat
from __future__ import unicode_literals
from __future__ import absolute_import
from __future__ import print_function

import os, sys, pygame
from pygame.locals import *

from random import seed, randint

sys.path.insert(0,'../vpoints')
from point2d import Point2d

###############
# Check the correct angle conversion for pygame!
###############
DEG = float(180.0 / 3.141592654)
seed()


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
        self.front = velocity.unit()
        self.left = Point2d(-self.front[1],self.front[0])
        
        # Seek target
        self.target = Point2d(10,10)
        
        # Angle of facing (degrees, polar coordinates)   
        #self.theta = angle_from_vector(self.front)
        
        # Rotational velocity (degrees per time)
        #self.omega = randint(-15,15)    
        
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
        theta = self.vel.angle()*DEG
        center = self.rect.center
        self.image = pygame.transform.rotate(self.orig,theta)
        self.rect = self.image.get_rect()
        self.rect.center = center
        
    def update(self,dt=1.0):
                
        # If we're within a certain distance of target, generate a new target
        if (self.pos - self.target).sqnorm() < self.maxspeed**2.1:
            self.target = Point2d(randint(10,sc_width-10),randint(10,sc_height-10))
            print('New target: %d, %d' % (self.target[0],self.target[1]))
        
        # Steering force calculated here (seeking behavior)
        if self.flee:
            sforce = flee_force(self,obj[0].pos) + seek_force(self,self.target)
        else:
            sforce = seek_force(self,self.target)
            
        sforce.truncate(self.maxforce)        
        accel = sforce.scale(1.0/self.mass)
        
        # Update velocity and heading
        self.vel = self.vel + accel
        self.vel.truncate(self.maxspeed)        
        
        # Align heading with velocity (unless velocity is very small)
        if self.vel.sqnorm() > .000000001:
            self.front = self.vel.unit()
            self.left = Point2d(-self.front[1],self.front[0])
            
        # Movement here
        self.move(dt)
        self.rotate(dt)
        
        # Simple edge-bouncing
        if False:
            if self.rect.left < 0 or self.rect.right > sc_width:
                self.vel = Point2d(-self.vel[0] ,self.vel[1])
                #self.omega = -self.omega
            if self.rect.top < 0 or self.rect.bottom > sc_height:
                self.vel = Point2d(self.vel[0], -self.vel[1])
                #self.omega = -self.omega

def seek_force(obj,tpos):
    """ Returns the steering force for obj to seek position tpos."""
    targetvel = tpos - obj.pos
    targetvel.normalize()
    targetvel = targetvel.scale(obj.maxspeed)
    return targetvel - obj.vel
        
def flee_force(obj,tpos):
    """ Returns the steering force for obj to flee from position tpos."""
    targetvel = obj.pos - tpos
    if 1 < targetvel.sqnorm() < 2500:
        targetvel.normalize()
        targetvel = targetvel.scale(obj.maxspeed)
        return targetvel - obj.vel 
    else:
        return Point2d(0,0)
        
if __name__ == "__main__":
    pygame.init()
    
    # Display constants
    size = sc_width, sc_height = 960, 800
    screen = pygame.display.set_mode(size)
    
    bgcolor = 111, 145, 192
    
    img, rec = load_image('pig.png',-1)
    angle = 0
    pos = Point2d(sc_width/2, sc_height/2)
    vel = Point2d(20,-20)
    
    # Create some objects
    n = 2
    obj = [MovingObject(img,rec,pos,20,vel) for i in range(n)]
    obj[0].flee = False
    obj[1].flee = True
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
