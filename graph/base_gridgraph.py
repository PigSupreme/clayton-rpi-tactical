#!/usr/bin/env python
"""
Basic GridGraph class.
Demo uses Pygame for rendering.
"""
from math import sqrt
INF = float('inf')

class GridGraph(object):
    """A regular rectangular grid with Manhattan/diagonal neighborhoods.

    Parameters
    ----------
    cols : int
        Number of node columns (in the horizontal dimension).
    rows : int
        Number of node rows (in the vertical dimension).
    dx : float
        Edge weight between horizontally adjacent nodes.
    dy : float
        Edge weight between vertically adjacent nodes.
    """
    def __init__(self, cols=2, rows=2, dx=1.0, dy=1.0):
        if rows < 2 or cols < 2:
            raise ValueError('Cannot create grid with %s rows, %s columns.' % (rows, cols))
        if dx < 0 or dy < 0:
            raise ValueError('Cannot create grid with dx = %s, dy = %s.' % (dx, dy))
        self._rows = rows
        self._cols = cols
        self._cost_x = dx
        self._cost_y = dy
        # Compute diagonal distance
        self._cost_d = sqrt(dx*dx + dy*dy)
        # List containing inactive/invalid nodes
        self.inactive = set()

    def is_node(self, node):
        """Check for a valid node (even if it's inactive)."""
        (x,y) = node
        if type(x)==int and type(y)==int and 0<x<=self._cols and 0<y<=self._rows:
            return True
        else:
            return False

    def is_not_inactive(self,(x,y)):
        """Check for an active node (does not check for validity).

        Note
        ----
        For performance reasons, this simply checks if the node with grid
        coordinates (x,y) is in the grid's inactive list.
        """
        return not (x,y) in self.inactive

    def edge_cost(self, node0, node1):
        """Get the edge cost between two nodes.
        Returns
        -------
        float: The edge cost, or INF if the nodes are not adjacent.

        Raises
        ------
        IndexError : If either node is invalid.
        """
        (x0,y0) = node0
        (x1,y1) = node1
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
                        return self._cost_y
                else: # xdist equals 1
                    if ydist == 0: # (xdist, ydist) equals (1,0)
                        return self._cost_x
                    else: # (xdist, ydist) equals (1,1)
                        return self._cost_d
            else: # If either node is inactive
                return INF
        else:
            raise IndexError('Invalid grid nodes (%s,%s) and/or (%s,%s) in %s.' % (x0,y0,x1,y1,self))

    def active_neighbors(self, node):
        """Get a list of active neighbors for the given node.

        Parameters
        ----------
        node: 2-tuple of int
            Grid coordinates of the given node.

        Note
        ----
        For performance reasons, this does not check if node is valid.
        """
        (i,j) = node
        nlist = []
        # Include nodes in a 3x3 square, centered at the given node,
        # but ignoring nodes past the grid boundary.
        for x in range(max(i-1,0), 1+min(i+1,self._cols)):
            for y in range(max(j-1,0), 1+min(j+1,self._rows)):
                if self.is_active((x,y)):
                    nlist.append((x,y))
        # If this node was active, we need to remove it from the above list.
        # This keeps the above loops simple.
        try:
            nlist.remove((i,j))
        except ValueError:
            pass

        return nlist

################ End of GridGraph class ##################

if __name__ == "__main__":

    ################ Pygame rendering functions ##############

    import pygame

    def draw_nodes(surface, xnum, ynum, color):
        """Draws the nodes of a recangular grid on a Pygame surface.

        Parameters
        ----------
        surface : pygame.Surface
            Surface on which to draw the graph.
        xnum : int
            Number of node columns (in the horizontal dimension).
        ynum : int
            Number of node rows (in the vertical dimension).
        color : pygame.Color
            Color of the nodes; must be compatible with surface colordepth.
        """
        (width, height) = surface.get_size()
        # Compute the distance between nodes on the display
        dx = width // (1+xnum)
        dy = height // (1+ynum)
        rad = max(min(dx,dy)//10,5)
        for xval in range(1, 1+xnum):
            for yval in range(1, 1+ynum):
                pygame.draw.circle(surface, color, (xval*dx,yval*dy), rad, 4)

    def draw_path(surface, nodelist, xnum, ynum, color):
        """Draws a path along nodes in a rectangular grid, on a Pygame surface.

        Parameters
        ----------
        surface : pygame.Surface
            Surface on which to draw the graph.
        nodelist : list of 2-tuples of int
            List of nodes in the path.
        xnum : int
            Number of node columns (in the horizontal dimension).
        ynum : int
            Number of node rows (in the vertical dimension).
        color : pygame.Color
            Color of the path; must be compatible with surface colordepth.
        Note
        ----
        This does not check any graph adjaceny information.
        """
        (width, height) = surface.get_size()
        # Compute the distance between nodes on the display
        dx = width // (1+xnum)
        dy = height // (1+ynum)
        # Convert grid coordinates to screen coordinates
        pointlist = [((x+1)*dx, (y+1)*dy) for (x,y) in nodelist]
        pygame.draw.lines(screen, color, False, pointlist, 5)

    ################ End of Pygame rendering ##################

    sample_graph = GridGraph(8, 5)

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
    draw_nodes(screen,grid_w,grid_h,nodecolor)
    sample_path = [(0,0),(0,1),(1,2),(1,3),(2,3),(3,3),(4,2)]
    draw_path(screen, sample_path, grid_w, grid_h, pathcolor)
    pygame.display.update()

    while 1:
        try:
            for event in pygame.event.get():
                if event.type in [pygame.MOUSEBUTTONDOWN]:
                    pygame.quit()
                    break
        except pygame.error:
            pygame.quit()
            break
