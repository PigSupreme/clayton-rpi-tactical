#!/usr/bin/env python
"""Tank control demo with SimpleRotatindMass2d"""

# for python3 compat
from __future__ import unicode_literals
from __future__ import absolute_import
from __future__ import print_function
from __future__ import division

import sys, pygame
from pygame.locals import *

INF = float('inf')

# TODO: Adjust this depending on where this file ends up.
sys.path.extend(['../vpoints', '../vehicle'])
from point2d import Point2d
from vehicle2d import load_pygame_image, SimpleRigidBody2d

class NewTank2d(SimpleRigidBody2d):

    def update(self,dt=1.0,tank_l=0.0,tank_r=0.0):
                        
        # Update velocity and heading
        vr = tank_l
        vl = tank_r
        
        # Tractive torque, based on difference in side vel's
        tractive_torque = (0.2)*(vl-vr)/self.radius
        
        damping_torque = (-0.6)*self.omega
        net_torque = tractive_torque + damping_torque
        
        # Tractive force (sum of both treads)
        tractive_force = self.front.scale(vr+vl)
        
        drag_force = self.vel.scale(-0.5)
        net_force = tractive_force + drag_force
    
        # Movement here
        self.move(dt, net_force)
        self.rotate(dt, net_torque)
        

pygame.init()
pygame.joystick.init()
joystick = pygame.joystick.Joystick(0)
joystick.init()

pygame.mouse.set_visible(False)

# Display constants
size = sc_width, sc_height = 960, 800
screen = pygame.display.set_mode(size)

bgcolor = 111, 145, 192

img, rec = load_pygame_image('tank.png',-1)
angle = 0
pos = Point2d(sc_width/2, sc_height/2)
vel = Point2d(0,0)

# Tank object
newtank = NewTank2d(pos,20,vel,0,0,(img,rec))

# Set-up Pygame rendering
rgroup = [newtank.sprite]
allsprites = pygame.sprite.RenderPlain(rgroup)

while 1:
    for event in pygame.event.get():
        if event.type in [QUIT]:
            pygame.quit()
            sys.exit()
    
    # Triangle to quit
    if joystick.get_button(3) == 1:
        pygame.quit()
        sys.exit()
        
    # X to reset tank position
    if joystick.get_button(1) == 1:
        newtank.pos = Point2d(sc_width/2,sc_height/2)

    # Compute tractive force from joystick input
    stick_l = -joystick.get_axis(1)*6
    stick_r = -joystick.get_axis(3)*6

    # Update vehicles first
    newtank.update(1.0, stick_l, stick_r)

    # Then update sprites
    allsprites.update(1.0) #,stick_l,stick_r)

    pygame.time.delay(50)

    # Render
    screen.fill(bgcolor)
    allsprites.draw(screen)
    pygame.display.flip()


pygame.time.delay(2000)