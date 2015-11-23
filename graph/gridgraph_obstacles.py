#!/usr/bin/env python
"""
NavGraph on a grid demo with dynamic circular obstacles and path-finding.
"""
import pygame
from pygame import Color
from pygame.locals import QUIT, MOUSEBUTTONDOWN

from math import sqrt
INF = float('INF')
FRAME_DELAY = 10

class NavGraphGrid(object):
    """Navigation graph on a rectangular grid graph, with diagonals.

    Nodes are in regularly-spaced rows and columns; each node is identified
    by its (x,y) coordinates.

    Parameters
    ----------
    cols : int
        Number of node columns (in the horizontal dimension).
    rows : int
        Number of node rows (in the vertical dimension).
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
            raise ValueError('Cannot create grid with %s rows, %s columns.' % (rows, cols))
        # World distances must be positive
        if cost_x <= 0 or cost_y <= 0:
            raise ValueError('Cannot create grid with cost_x = %s, cost_y = %s.' % (cost_x, cost_y))

        self._rows = rows
        self._cols = cols
        self._cost_x = cost_x
        self._cost_y = cost_y
        self._cost_d = sqrt(cost_x*cost_x + cost_y*cost_y)   # Diagonal distance
        self._nr = noderad
        self._inactive = set() # Set of currently inactive nodes

    def is_node(self, (x,y)):
        """Check for a valid node (even if it's inactive)."""
        if type(x)==int and type(y)==int and 0<x<=self._cols and 0<y<=self._rows:
            return True
        else:
            return False

    def is_not_inactive(self, (x,y)):
        """Check for an active node (does not check for validity).

        Note
        ----
        For performance reasons, this simply checks if the node with grid
        coordinates (x,y) is in the grid's inactive list.
        """
        return not (x,y) in self._inactive

    def edge_cost(self, (x0,y0), (x1,y1)):
        """Get the edge cost between two nodes.
        Returns
        -------
        float: The edge cost, or INF if the nodes are not adjacent.

        Raises
        ------
        IndexError : If either node is invalid.
        """
        if self.is_node((x0,y0)) and self.is_node((x1,y1)):
            if self.is_not_inactive((x0,y0)) and self.is_not_inactive((x1,y1)):
                xdist = abs(x0-x1)
                ydist = abs(y0-y1)
                if xdist > 1 or ydist > 1:
                    return INF
                if xdist == 0:
                    if ydist == 0:
                        return 0
                    else: # (xdist, ydist) equals (0,1)
                        return self._cost_y
                else: # xdist equals 1
                    if ydist == 0: # (xdist, ydist) equals (1,0)
                        return self._cost_x
                    else: # (xdist, ydist) equals (1,1)
                        return self._cost_d
            else: # If either node is inactive
                return INF
        else:
            raise IndexError('Invalid grid nodes (%s,%s) and/or (%s,%s) in %s.' % (x0, y0, x1, y1, self))

    def active_neighbors(self, (i,j)):
        """Get a list of active neighbors for the given node.
        Paramters
        ---------
        node: 2-tuple of int
            Grid coordinates of the given node.
        """
        nlist = []
        # Look at nodes in a 3x3 square, centered at the given node
#        for x in range(i-1,i+2):
#            for y in range(j-1,j+2):
        for x in range(max(1, i-1), 1 + min(i+1, self._cols)):
            for y in range(max(1, j-1), 1 + min(j+1, self._rows)):
                if self.is_node((x,y)) and self.is_not_inactive((x,y)):
                    nlist.append((x,y))
        # If this node was active, we need to remove it from the above list.
        try:
            nlist.remove((i,j))
        except ValueError:
            pass

        return nlist

    def world_distance(self, (x0,y0), (x1,y1)):
        """Get the world (Euclidan, symmetric) distance between two nodes.
        Parameters
        ----------
        node0: 2-tuple of int
            Grid coordinates of the firt node.
        node1: 2-tuple of int
            Grid coordinates of the second node.
        """
        return sqrt(((x0-x1)*self._cost_x)**2 + ((y0-y1)*self._cost_y)**2)

    def find_path(self, start, finish):
        """Shortest path between start and finish, using Dijkstra.
        Returns
        -------
        list : Grid coordinates of nodes on the shortest path, including start/finish.
        """
        if not (self.is_not_inactive(start) and self.is_not_inactive(finish)):
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
                    nodedist = settledist + self.edge_cost(settlenow, node)
                    if node not in frontier or frontier[node] > nodedist:
                        frontier.update({node:nodedist})
                        parents.update({node:settlenow})

            # Find the nearest node on the frontier
            # Empty frontier triggers the ValueError and returns empty path
            try:
                settlenow = min(frontier, key=frontier.get)
            except ValueError:
                return []

        # Output shortest path here
        minpath = [finish]
        node = finish
        while node in parents:
            node = parents[node]
            minpath.insert(0, node)

        return minpath

    ############################################################
    #### Active node management/obstacle detection functions
    ############################################################

    def activate_all_nodes(self):
        """Sets all nodes in the graph to active."""
        self._inactive = set()

    def avoid_circle(self, surface, (h,k,r)):
        """Deactivates nodes that intersect a given circle.
        (h,k) is the circle center, in screen coordinates
        r is the circle radius, in pixels."""
        (width, height) = surface.get_size()
        dx = width // (1+self._cols)
        dy = height // (1+self._rows)
        for i in range(1, 1+self._cols):
            for j in range(1, 1+self._rows):
                (x,y) = (i*dx, j*dy)
                if (x-h)**2 + (y-k)**2 <= (r + self._nr)**2:
                    self._inactive.add((i,j))

    def avoid_cone(self, surface, (x0,y0), (x1,y1), (x2,y2)):
        """Deactivates points within a given cone. INCOMPLETE.

        Note
        ----
        Function was not working as written. Fix later or use the cone model
        from gridgraph_spotlight. Raises NotImplementedError.
        """
        raise NotImplementedError
        (width, height) = surface.get_size()
        dx = width // (1+self._cols)
        dy = height // (1+self._rows)
        for i in range(1, 1+self._cols):
            for j in range(1, 1+self._rows):
                # Compute local coordinates (a,b):
                (a,b) = (i*dx-x0, j*dy-y0)
                # If anticlockwise of v1 and clockwise of v2
                if (x1*b-y1*a < 0) and (x2*b-y2*a > 0):
                    self._inactive.add((i,j))

    ############################################################
    #### Pygame rendering functions start here
    ############################################################

    def draw_nodes(self, surface, color1, color2):
        """Render the grid nodes on a Pygame.surface, automatic spacing."""
        (width, height) = surface.get_size()
        # Compute the distance between nodes on the display
        dx = width // (1+self._cols)
        dy = height // (1+self._rows)
        rad = int(self._nr)
        for i in range(1, 1+self._cols):
            for j in range(1, 1+self._rows):
                if self.is_not_inactive((i,j)):
                    pygame.draw.circle(surface, color1, (i*dx,j*dy), rad)
                else:
                    pygame.draw.circle(surface, color2, (i*dx,j*dy), rad, 4)

    def draw_path(self,surface, nodelist, color):
        """Draws a path along nodelist on a Pygame.surface, automatic spacing."""
        (width, height) = surface.get_size()
        # Compute the distance between nodes on the display
        dx = width // (1+self._cols)
        dy = height // (1+self._rows)

        pointlist = [(i*dx,j*dy) for (i,j) in nodelist]
        pygame.draw.lines(surface, color, False, pointlist,5)


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

    # Sample grid, with x and y costs based on screen dimensions.
    x_dist = scr_w // (1+grid_w)
    y_dist = scr_h // (1+grid_h)
    sample_grid = NavGraphGrid(grid_w,grid_h,x_dist,y_dist)

    # Dynamic Obstacles Set-up
    obs_list = [(x,300-x,(5-2*x)//14+2,(5+x)%12+5,x+15) for x in range(20,150,30)]
    pygame.event.clear()

    # Main loop
    b_done = False
    while not b_done:

        for event in pygame.event.get():
            if event.type in [QUIT, MOUSEBUTTONDOWN]:
                b_done = True
                break
        screen.fill(bgcolor)

        # Set all nodes to active before we do any collision detection
        sample_grid.activate_all_nodes()

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
            sample_grid.avoid_circle(screen,(h,k,r))

            # Render this obstacle
            pygame.draw.circle(screen,obscolor,(h,k),r,1)

        # Find a new path
        path = sample_grid.find_path((1,1),(grid_w,grid_h))

        # Redraw
        sample_grid.draw_nodes(screen,nodecolor,inactivecolor)
        if path:
            sample_grid.draw_path(screen,path,pathcolor)
        pygame.display.update()
        pygame.time.delay(FRAME_DELAY)

    # Clean-up here
    pygame.quit()



