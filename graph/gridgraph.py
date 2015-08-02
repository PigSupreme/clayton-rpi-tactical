# -*- coding: utf-8 -*-
"""
Basic grid graph demo using pygame for rendering.

TODO: This code is probably duplicated elsewhere...check that.
"""
import pygame
from math import sqrt
INF = float('inf')

class gridgraph:
    def __init__(self,cols=2,rows=2,dx=1.0,dy=1.0):
        if rows < 2 or cols < 2:
            raise ValueError('Cannot create grid with %s rows, %s columns.' % (rows,cols))
        if dx < 0 or dy < 0:
            raise ValueError('Cannot create grid with dx = %s, dy = %s.' % (dx,dy))
        self.rows = rows
        self.cols = cols
        self.dx = dx
        self.dy = dy
        # Compute diagonal distance
        self.dd = sqrt(dx*dx + dy*dy)
        # List containing inactive/invalid nodes
        self.inactive=[]

    def is_node(self,x,y):
        """Returns True if (x,y) is a valid node in this gridgraph."""
        if type(x)==int and type(y)==int and 0 <= x < self.cols and 0 <= y < self.rows:
            return True
        else:
            return False

    def is_active(self,x,y):
        """Returns False if node (x,y) is on the inactive list for this graph."""
        return not (x,y) in self.inactive

    def edge_cost(self,x0,y0,x1,y1):
        """Returns the edge cost between nodes at (x0,y0) and (x1,y1)."""
        if self.is_node(x0,y0) and self.is_node(x1,y1):
            xdist = abs(x0-x1)
            ydist = abs(y0-y1)
            if xdist > 1 or ydist > 1:
                return INF
            if xdist == 0:
                if ydist == 0:
                    return 0
                else: # (xdist, ydist) equals (0,1)
                    return self.dy
            else: # xdist equals 1
                if ydist == 0: # (xdist, ydist) equals (1,0)
                    return self.dx
                else: # (xdist, ydist) equals (1,1)
                    return self.dd
        else:
            raise IndexError('Invalid grid nodes (%s,%s) and/or (%s,%s) in %s.' % (x0,y0,x1,y1,self))


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

    g = gridgraph(8,5)

    # Display window resolution
    scr_w, scr_h = 640, 480

    # Grid size and colors
    grid_w, grid_h = 8, 5
    nodecolor = 0,200,0
    pathcolor = 0,0,200

    # Pygame initiailzation (pygame has alredy been imported)
    pygame.init()
    screen = pygame.display.set_mode((scr_w,scr_h))

    # Sample path
    drawnodes(screen,grid_w,grid_h,nodecolor)
    drawpath(screen,[(0,0),(0,1),(1,2),(1,3),(2,3),(3,3),(4,2)],grid_w,grid_h,pathcolor)
    pygame.display.update()

