#!/usr/bin/python
"""
Created on Wed Apr 15 17:51:23 2015

@author: mdancs
"""
import pygame
from pygame import Color
from pygame.locals import *

from math import sqrt, cos, sin

def draw_ray(surface,color,(x,y),(a,b)):
    """Draw a ray from a given point in a given direction."""
    rlen = 2000
    pygame.draw.line(surface,color,(x,y),(x+rlen*a,y+rlen*b))

class cone_block:
    def __init__(self,x0=0,y0=0,theta=0,delmax=0.5,phi=0.1,omega=0.053):
        self.x = x0
        self.y = y0
        self.theta = theta
        self.delmax = abs(delmax)
        self.phi = abs(phi)
        self.omega = omega
        self.vr = (cos(theta),sin(theta))
        self.vl = (cos(theta+phi),sin(theta+phi))
        
    def update(self,dt=1.0):
        theta = self.theta + self.omega * dt
        if abs(theta) > self.delmax:
            self.omega = -self.omega
        self.vl = (cos(theta),sin(theta))
        self.vr = (cos(theta+self.phi),sin(theta+self.phi))
        
    def get_cone(self):
        return [self.theta,(self.x0,self.y0),self.vl,self.vr]
            
        


class gridgraph:
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
        """Returns True if (x,y) is a valid node in this gridgraph."""
        if type(x)==int and type(y)==int and 0 <= x < self.cols and 0 <= y < self.rows:
            return True
        else:
            return False
    
    def is_active(self,(x,y)):
        """Returns False if node (x,y) is on the inactive list for this graph."""
        return not (x,y) in self.inactive

    def edge_cost(self,(x0,y0),(x1,y1)):
        """Returns the edge cost between nodes at (x0,y0) and (x1,y1)."""
        if self.is_node(x0,y0) and self.is_node(x1,y1):
            if self.is_active((x0,y0)) and self.is_active((x1,y1)):
                xdist = abs(x0-x1)
                ydist = abs(y0-y1)
                if xdist > 1 or ydist > 1:
                    return inf
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
            else: # If either node is inactive
                return inf
        else:
            raise IndexError('Invalid grid nodes (%s,%s) and/or (%s,%s) in %s.' % (x0,y0,x1,y1,self))
            
    def active_neighbors(self,node):
        """Returns the list of active neighbors to the given node."""
        (i,j) = node
        nlist = []
        for x in range(i-1,i+2):
            for y in range(j-1,j+2):
                if self.is_node(x,y) and self.is_active((x,y)):
                    nlist.append((x,y))
        try:
            nlist.remove((i,j))            
        except ValueError:
            pass
        
        return nlist
            
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
            
    def find_path(self,start,finish):
        """Shortest path between start and finish, using Dijkstra."""
        if not (self.is_active(start) and self.is_active(finish)):
            return []
        settled = {}
        frontier = {start:0}
        parents = {}
        settlenow = start
        
        while settlenow != finish:        
            # Settle a node in the frontier
        
            settledist = frontier.pop(settlenow)
            settled.update({settlenow:settledist})
            
            # Update neighbors of the node we just settled
            nnnn = self.active_neighbors(settlenow)
            for node in nnnn:
                if node not in settled:
                    nodedist = settledist + self.edge_cost(settlenow,node)
                    if node not in frontier or frontier[node] > nodedist:
                        frontier.update({node:nodedist})
                        parents.update({node:settlenow})
                    
            # Find the nearest node on the frontier
            # Empty frontier triggers the ValueError and returns empty path
            try:
                settlenow = min(frontier,key=frontier.get)
            except ValueError:
                return []
            
        # Output shortest path here
        minpath = [finish]
        node = finish
        while node in parents:
            node = parents[node]
            minpath.append(node)
            
        minpath.reverse()
        return minpath            
        
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
             
    def draw_path(self,surface,nodelist,color):
        """Draws a path along nodelist on a xnum by ynum grid in surface, automatic spacing."""
        (width, height) = surface.get_size()
        # Compute the distance between nodes on the display
        dx = width // (1+self.cols)
        dy = height // (1+self.rows)
        
        pointlist = [((i)*dx,(j)*dy) for (i,j) in nodelist]
        pygame.draw.lines(surface,color,False,pointlist,5)


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

    # Pygame initiailzation (pygame has alredy been imported)
    pygame.init()
    screen = pygame.display.set_mode((scr_w,scr_h))

    # Sample grid   
    g = gridgraph(grid_w,grid_h)

    
    # Dynamic Obstacles
    theta0 = 0.25
    omega0 = 0.0561
    
    cones = [[-3.14/2,(0,0),(1,2),(1,1)],[omega0,(scr_w // 2,scr_h),(1,1),(2,1)]]
    #cones = [[(0,0),(1,2),(1,1)],[(0,scr_h),(2,-1),(1,-1)],[(scr_w,0),(-2,1),(-2,1.5)]]
    
    pygame.event.clear()
    pygame.event.set_blocked(MOUSEMOTION)
    while 1:
        
        #pygame.event.wait()
        screen.fill(bgcolor)     

        g.deactivate_all_nodes()

        theta = theta0
        omega = omega0
            
        # Deactive nodes within this cone:
        new_cones = list()
        for [t,p0,vl,vr] in cones[:]:                      
            g.outside_cone(screen,p0,vl,vr)
            draw_ray(screen,pathcolor,p0,vl)
            draw_ray(screen,pathcolor,p0,vr)

            t = t + omega
            if t > 6.28:
                t = t - 6.28
            newcone = [t,p0,(cos(t),-sin(t))]
            t = t + theta
            if t > 6.28:
                t = t - 6.28
            newcone.append((cos(t),-sin(t)))
            new_cones.append(newcone)
            
            omega = omega - 0.0147
            
        cones = new_cones
                
                

        # Find a new path        
        path = g.find_path((1,1),(grid_w-1,grid_h-1))  

            
        # Redraw
        g.draw_nodes(screen,nodecolor,obscolor)
        if path:
            pass
            #g.draw_path(screen,path,pathcolor)
        pygame.display.update()
        pygame.time.delay(60)
        
    # Clean-up here
    pygame.quit()

    
    
    