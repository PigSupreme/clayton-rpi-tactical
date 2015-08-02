# -*- coding: utf-8 -*-
"""
Created on Wed Apr 15 17:51:23 2015

@author: mdancs
"""
import pygame

def drawnodes(surface,xnum,ynum,color):
    """Draws a grid of xnum by ynum nodes on surface, automatic spacing"""
    (width, height) = surface.get_size()
    # Compute the distance between nodes on the display
    dx = width // (1+xnum)
    dy = height // (1+ynum)
    rad = max(min(dx,dy)//10,5)
    for xval in range(1,1+xnum):
        for yval in range(1,1+ynum):
            pygame.draw.circle(surface,color,(xval*dx,yval*dy),rad,4)
             
def drawpath(surface,nodelist,xnum,ynum,color):
    """Draws a path along nodelist on a xnum by ynum grid in surface"""
    (width, height) = surface.get_size()
    # Compute the distance between nodes on the display
    dx = width // (1+xnum)
    dy = height // (1+ynum)
    
    pointlist = [((x+1)*dx,(y+1)*dy) for (x,y) in nodelist]
    pygame.draw.lines(screen,color,False,pointlist,5)

if __name__ == "__main__":
    # Display window resolution
    scr_w, scr_h = 640, 480
    
    # Grid size and colors
    grid_w, grid_h = 8, 5
    nodecolor = 0,200,0
    pathcolor = 0,0,200

    # Pygame initiailzation
    pygame.init()
    screen = pygame.display.set_mode((scr_w,scr_h))

    # Sample path   
    drawnodes(screen,grid_w,grid_h,nodecolor)
    drawpath(screen,[(0,0),(0,1),(1,2),(1,3),(2,3),(3,3),(4,2)],grid_w,grid_h,pathcolor)
    pygame.display.update()