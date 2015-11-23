#!/usr/bin/env python
"""
Another GridGraphDemo demo; finds nodes in the intersection of several cones.
TODO: Update with changes from base_gridgraph and gridgraph_obstacles.
"""
import pygame
from pygame import Color
from pygame.locals import QUIT, MOUSEBUTTONDOWN

from math import sqrt, cos, sin

FRAME_DELAY = 100

def draw_ray(surface,color,(x,y),(a,b),rlen=2000):
    """Draw a ray from a given point in a given direction."""
    pygame.draw.line(surface,color,(x,y),(x+rlen*a,y+rlen*b))

class ConeBlock(object):
    """Demo cone class using vertex, direction, and spanning angle."""
    def __init__(self,x0=0,y0=0,theta=0.6,omega=0.0273,phi=0.341):
        self.x0 = x0
        self.y0 = y0
        self.theta = theta
        self.delta = 0
        self.delmax = 0.618
        self.phi = abs(phi)
        self.omega = omega
        self.vr = (cos(theta),sin(theta))
        self.vl = (cos(theta+phi),sin(theta+phi))

    def update(self,dt=1.0):
        delta = self.delta + self.omega * dt
        if abs(delta) > self.delmax:
            self.omega = -self.omega
        theta = self.theta + delta
        self.vr = (cos(theta),sin(theta))
        self.vl = (cos(theta+self.phi),sin(theta+self.phi))
        self.delta = delta

    def get_cone(self):
        return [self.theta,(self.x0,self.y0),self.vl,self.vr]

class GridGraphDemo(object):
    def __init__(self,cols=2,rows=2,dx=6,dy=5,noderad=5.0):
        if rows < 2 or cols < 2:
            raise ValueError('Cannot create grid with %s rows, %s columns.' % (rows,cols))
        if dx < 0 or dy < 0:
            raise ValueError('Cannot create grid with dx = %s, dy = %s.' % (dx,dy))
        self.rows = rows
        self.cols = cols
        self.dx = dx
        self.dy = dy
        self.dd = sqrt(dx*dx + dy*dy)   # Diagonal distance
        self.nr = noderad   # Bounding radius of each node
        self.inactive=set() # Set of currently inactive nodes

    def is_node(self,x,y):
        """Returns True if (x,y) is a valid node in this GridGraphDemo."""
        if type(x)==int and type(y)==int and 0 <= x <= self.cols and 0 <= y <= self.rows:
            return True
        else:
            return False

    def is_active(self,(x,y)):
        """Returns False if node (x,y) is on the inactive list for this graph."""
        return not (x,y) in self.inactive

    def world_distance(self,start,finish):
        """Returns the world (Euclidan) distance between two nodes.
        start, finish should each be an (row,col) tuple."""
        (x0,y0) = start
        (x1,y1) = finish
        return sqrt(((x0-x1)*self.dx)**2 + ((y0-y1)*self.dy)**2)

    def deactivate_all_nodes(self):
        self.inactive=set()
        for i in range(1,1+self.cols):
            for j in range(1,1+self.rows):
                self.inactive.add((i,j))

    def avoid_circle(self,surface,(h,k,r)):
        """Deactivates nodes that intersect a given circle.
        (h,k) is the circle center, in screen coordinates
        r is the circle radius, in pixels."""
        (width, height) = surface.get_size()
        dx = width // (1+self.cols)
        dy = height // (1+self.rows)
        for i in range(1,1+self.cols):
            for j in range(1,1+self.rows):
                (x,y) = (i*dx,j*dy)
                if (x-h)**2 + (y-k)**2 <= (r + self.nr)**2:
                    self.inactive.add((i,j))

    def outside_cone(self,surface,(x0,y0),(x1,y1),(x2,y2)):
        """Activates points outside of a given cone."""
        (width, height) = surface.get_size()
        dx = width // (1+self.cols)
        dy = height // (1+self.rows)
        for i in range(1,1+self.cols):
            for j in range(1,1+self.rows):
                # Compute local coordinates (a,b):
                (a,b) = (i*dx-x0,j*dy-y0)
                # If anticlockwise of v1 and clockwise of v2
                if (x1*b-y1*a > 0) or (x2*b-y2*a < 0) :
                    try:
                        self.inactive.remove((i,j))
                    except KeyError:
                        pass

    def draw_nodes(self,surface,color1,color2):
        """Draws a grid of xnum by ynum nodes on surface, automatic spacing."""
        (width, height) = surface.get_size()
        # Compute the distance between nodes on the display
        dx = width // (1+self.cols)
        dy = height // (1+self.rows)
        rad = int(self.nr)
        for i in range(1,1+self.cols):
            for j in range(1,1+self.rows):
                if self.is_active((i,j)):
                    pygame.draw.circle(surface,color1,(i*dx,j*dy),rad)
                else:
                    pygame.draw.circle(surface,color2,(i*dx,j*dy),rad,4)


if __name__ == "__main__":

    # Display window resolution
    scr_w, scr_h = 1080, 800

    # Grid size and colors
    grid_w, grid_h = 18, 15
    bgcolor = Color(0,0,0)
    nodecolor = Color(0,200,0)
    inactivecolor = Color(55,55,55)
    pathcolor = Color(0,0,200)
    obscolor = Color(234,0,0)

    # Pygame initiailzation
    pygame.init()
    screen = pygame.display.set_mode((scr_w,scr_h))

    # Sample grid
    sample_grid = GridGraphDemo(grid_w,grid_h)

    # Dynamic Obstacles
    theta0 = 0.25
    omega0 = 0.0561

    conelist = [ConeBlock(-75,-75,0.2),ConeBlock(scr_w+75,scr_h//2,3.14,-0.0461),ConeBlock(scr_w//5,scr_h+75,-1.34)]

    b_done = False
    while not b_done:

        for event in pygame.event.get():
            if event.type in [QUIT, MOUSEBUTTONDOWN]:
                b_done = True
                break
        screen.fill(bgcolor)

        sample_grid.deactivate_all_nodes()

        # Deactive nodes within this cone:
        for a in conelist:
            a.update()
            [t,p0,vl,vr] = a.get_cone()
            sample_grid.outside_cone(screen,p0,vl,vr)
            draw_ray(screen,pathcolor,p0,vl)
            draw_ray(screen,pathcolor,p0,vr)

        # Redraw
        sample_grid.draw_nodes(screen,nodecolor,obscolor)

        pygame.display.update()
        pygame.time.delay(FRAME_DELAY)

    # Clean-up here
    pygame.quit()



