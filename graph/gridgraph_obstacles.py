#!/usr/bin/env python
"""
Grid graph demo with cost_ynamic obstacles and path-finding.
"""
import sys

import pygame
from pygame import Color
from pygame.locals import *

from math import sqrt
INF = float('INF')
FRAME_DELAY = 10

class NavGraphGrid(object):
    """Navigation graph on a rectangular grid graph, with diagonals.

    Nodes are in regularly-spaced rows and columns; each node is identified
    by its (x,y) coordinates.

    Parameters
    ----------
    cols: int
        Number of columns (x-direction).
    rows: int
        Number of rows (y-direction).
    cost_x:
        Travel cost between horizontally adjacent nodes.
    cost_y:
        Travel cost between vertically adjacent nodes.
    noderad: float
        Pixel radius of each node; used for rendering/collision detection.
    """

    def __init__(self, cols=2, rows=2, cost_x=6, cost_y=5, noderad=5.0):
        # Error-checking
        # Grid must be at least 2 x 2
        if rows < 2 or cols < 2:
            raise ValueError('Cannot create grid with %s rows, %s columns.' % (rows,cols))
        # World distances must be positive
        if cost_x <= 0 or cost_y <= 0:
            raise ValueError('Cannot create grid with cost_x = %s, cost_y = %s.' % (cost_x,cost_y))

        self.rows = rows
        self.cols = cols
        self.cost_x = cost_x
        self.cost_y = cost_y
        self.dd = sqrt(cost_x*cost_x + cost_y*cost_y)   # Diagonal distance
        self.nr = noderad
        self.inactive=set() # Set of currently inactive nodes

    def is_node(self,x,y):
        """Check for a valid node (even if it's inactive)."""
        if type(x)==int and type(y)==int and 0 <= x < self.cols and 0 <= y < self.rows:
            return True
        else:
            return False

    def is_active(self,(x,y)):
        """Check for an active node (does not check for validity).
        Notes
        -----
        Validity could be checked with is_node(), but skipped for performance.
        """
        return not (x,y) in self.inactive

    def edge_cost(self,(x0,y0),(x1,y1)):
        """Get the edge cost between two nodes.
        Returns
        -------
        float: The edge cost, or INF if the nodes are not adjacent.

        Raises
        ------
        IndexError : If either node is invalid.
        """
        if self.is_node(x0,y0) and self.is_node(x1,y1):
            if self.is_active((x0,y0)) and self.is_active((x1,y1)):
                xdist = abs(x0-x1)
                ydist = abs(y0-y1)
                if xdist > 1 or ydist > 1:
                    return INF
                if xdist == 0:
                    if ydist == 0:
                        return 0
                    else: # (xdist, ydist) equals (0,1)
                        return self.cost_y
                else: # xdist equals 1
                    if ydist == 0: # (xdist, ydist) equals (1,0)
                        return self.cost_x
                    else: # (xdist, ydist) equals (1,1)
                        return self.dd
            else: # If either node is inactive
                return INF
        else:
            raise IndexError('Invalid grid nodes (%s,%s) and/or (%s,%s) in %s.' % (x0,y0,x1,y1,self))

    def active_neighbors(self,node):
        """Get a list of active neighbors for the given node.
        Paramters
        ---------
        node: 2-tuple of int
            Grid coordinates of the given node.
        """
        (i,j) = node
        nlist = []
        # Look at nodes in a 3x3 square, centered at the given node
        for x in range(i-1,i+2):
            for y in range(j-1,j+2):
                # TODO: is_node() is needed for boundary nodes. Would it be
                # worthwhile to speed this up with extra checking?
                if self.is_node(x,y) and self.is_active((x,y)):
                    nlist.append((x,y))
        # If this node was active, we need to remove it from the above list.
        try:
            nlist.remove((i,j))
        except ValueError:
            pass

        return nlist

    def world_distance(self, node0, node1):
        """Get the world (Euclidan, symmetric) distance between two nodes.
        Parameters
        ----------
        node0: 2-tuple of int
            Grid coordinates of the firt node.
        node1: 2-tuple of int
            Grid coordinates of the second node.
        """
        (x0,y0) = node0
        (x1,y1) = node1
        return sqrt(((x0-x1)*self.cost_x)**2 + ((y0-y1)*self.cost_y)**2)

    def find_path(self,start,finish):
        """Shortest path between start and finish, using Dijkstra.        
        Returns
        -------
        list : Grid coordinates of nodes on the shortest path, including start/finish.
        """        
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
            minpath.insert(0,node)
            
        return minpath

    ############################################################
    #### Active node management/obstacle detection functions
    ############################################################

    def activate_all_nodes(self):
        """Sets all nodes in the graph to active."""
        self.inactive = set()

    def avoid_circle(self,surface,(h,k,r)):
        """Deactivates nodes that intersect a given circle.
        (h,k) is the circle center, in screen coordinates
        r is the circle radius, in pixels."""
        (width, height) = surface.get_size()
        cost_x = width // (1+self.cols)
        cost_y = height // (1+self.rows)
        for i in range(1,1+self.cols):
            for j in range(1,1+self.rows):
                (x,y) = (i*cost_x,j*cost_y)
                if (x-h)**2 + (y-k)**2 <= (r + self.nr)**2:
                    self.inactive.add((i,j))

    def avoid_cone(self,surface,(x0,y0),(x1,y1),(x2,y2)):
        """Deactivates points within a given cone."""
        (width, height) = surface.get_size()
        cost_x = width // (1+self.cols)
        cost_y = height // (1+self.rows)
        for i in range(1,1+self.cols):
            for j in range(1,1+self.rows):
                # Compute local coordinates (a,b):
                (a,b) = (i*cost_x-x0,j*cost_y-y0)
                # If anticlockwise of v1 and clockwise of v2
                if (x1*b-y1*a > 0)  and True:
                    self.inactive.add((i,j))

    ############################################################
    #### Pygame rendering functions start here
    ############################################################

    def draw_nodes(self, surface, color1, color2):
        """Draws a grid of xnum by ynum nodes on surface, automatic spacing."""
        (width, height) = surface.get_size()
        # Compute the distance between nodes on the display
        cost_x = width // (1+self.cols)
        cost_y = height // (1+self.rows)
        rad = int(self.nr)
        for i in range(1,1+self.cols):
            for j in range(1,1+self.rows):
                if self.is_active((i,j)):
                    pygame.draw.circle(surface,color1,(i*cost_x,j*cost_y),rad)
                else:
                    pygame.draw.circle(surface,color2,(i*cost_x,j*cost_y),rad,4)

    def draw_path(self,surface,nodelist,color):
        """Draws a path along nodelist on a xnum by ynum grid in surface, automatic spacing."""
        (width, height) = surface.get_size()
        # Compute the distance between nodes on the display
        cost_x = width // (1+self.cols)
        cost_y = height // (1+self.rows)

        pointlist = [((i)*cost_x,(j)*cost_y) for (i,j) in nodelist]
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

    # Pygame initiailzation
    pygame.init()
    screen = pygame.display.set_mode((scr_w,scr_h))

    # Sample grid
    # TODO: Set edge costs based on grid size and world dimensions??
    g = NavGraphGrid(grid_w,grid_h)

    # Dynamic Obstacles Set-up
    obs_list = [(x,300-x,(5-2*x)//14+2,(5+x)%12+5,x+15) for x in range(20,150,30)]
    pygame.event.clear()

    while 1:

        for event in pygame.event.get():
            if event.type in [QUIT, MOUSEBUTTONDOWN]:
                pygame.quit()
                sys.exit()
        screen.fill(bgcolor)

        # Set all nodes to active before we do any collision detection
        g.activate_all_nodes()

        # Update loop for dynamic obstacles
        for i in range(len(obs_list)):

            # Motion with basic edge bouncing
            (h,k,vx,vy,r) = obs_list[i]
            h = h + vx
            k = k + vy
            # Edge bounce
            if not (0 <= h < scr_w):
                vx = -vx
            if not (0 <= k < scr_h):
                vy = -vy
            # Update obstacle's position/velocity
            obs_list[i] = (h,k,vx,vy,r)

            # Deactive nodes blocked by this obstacle
            g.avoid_circle(screen,(h,k,r))

            # Render this obstacle
            pygame.draw.circle(screen,obscolor,(h,k),r,1)

        # Find a new path
        path = g.find_path((1,1),(grid_w-1,grid_h-1))

        # Redraw
        g.draw_nodes(screen,nodecolor,inactivecolor)
        if path:
            g.draw_path(screen,path,pathcolor)
        pygame.display.update()
        pygame.time.delay(FRAME_DELAY)

    # Clean-up here
    pygame.quit()



