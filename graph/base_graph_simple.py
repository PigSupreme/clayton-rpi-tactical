#!/usr/bin/env python
"""
Lightweight classes for graphs with anonymous edges.
"""
import pygame

class SimpleGraphNode(object):
    """Base class for nodes in a simple, undirected graph.

    Parameters
    ----------
    node_id: int
        ID to assign this node. Allow consistency with external information.
        See below for further information.

    Notes
    -----
    The class itself keeps a master dictionary (node_from_id), that can be
    used to obtain a reference to the node with a given id. The implementation
    requires that ID's are nonnegative integers and are used in increasing
    order. ID's that are skipped over cannot be used later.
    
    Additional attributes can be set using optional keyword arguments. Each
    key (except node_id) sets an instance variable with the same name. There
    is no error-checking, but subclasses may override this.

    Note
    ----
    This class is intended for graphs with no edge information. Each node will
    keep track of its neighbors (using an adjacency set, no duplicates), so we
    do not need any other classes to manage the graph topology.
    """

    INVALID_NODE_ID = -1
    """Any reference to this index is treated as being a nonexistant node."""

    # This is used as a class variable, so that each node has a unique ID.
    _NEXT_NODE_ID = 0

    # This is the directory of nodes by index, without needing a manager.
    # To invalidate ID n, use SimpleGraphNode.node_from_id[n] = None
    node_from_id = {INVALID_NODE_ID: None}

    def __init__(self, node_id, **kwargs):
        """Creates a graph node, sets its ID and any extra information."""
        if node_id >= SimpleGraphNode._NEXT_NODE_ID:
            self._node_id = node_id
            SimpleGraphNode.node_from_id[node_id] = self
            SimpleGraphNode._NEXT_NODE_ID = node_id + 1
            self._adjacent = set()
        else:
            raise ValueError('Node ID %d is already in use.' % node_id)
        # Set any extra information
        for key in kwargs:
            if key is not 'node_id':
                self.key = kwargs[key]

    def get_id(self):
        """Returns the ID of this node."""
        return self._node_id

    def get_neighbors(self):
        """Returns a list of nodes (not ID's!) adjacent to this one."""
        
        # Because the neighbors might become invalid without this node knowing,
        # we really do need to use node_from_id[] below
        result = []
        for neigh_id in self._adjacent:
            node = SimpleGraphNode.node_from_id[neigh_id]
            if node is not None:
                result.append(node)
        return result

    def ignore_me(self):
        """Sets this node to be treated as temporarily inactive.
        
        Note
        ----
        
        After calling this, existing references to this node will remain valid,
        but any future queries to node_from_id[] will return None. This gives
        the ability to temporarily ignore nodes without the overhead of
        deleting them. Provided that we keep an external reference, we can
        reactivate this node later, using unignore_me() below.
        """
        SimpleGraphNode.node_from_id[self._node_id] = None

    def unignore_me(self):
        """Restore this node to being treated as active.
        
        Note
        ----
        
        After calling this, any information about this node (including edges
        to/from adjacent nodes) that existed before make_invalid() will once
        again be available.
        """
        SimpleGraphNode.node_from_id[self._node_id] = self

    def connect_to(self, *neighbor_ids):
        """Add an undirected (two-way) edge from this node to other(s).

        Parameters
        ----------
        
        *neighbor_ids : int or sequence of int
            ID(s) of node(s) to make adjacent to this one, possibly empty.
        """
        for neigh_id in neighbor_ids:
            neigh = SimpleGraphNode.node_from_id[neigh_id]
            if neigh is not None:
                self._adjacent.add(neigh_id)
                neigh._adjacent.add(self._node_id)

    def disconnect_from(self, *neighbor_ids):
        """Removes edges from this node to/from its neighbors.

        Parameters
        ----------
        
        *neighbor_ids : int or sequence of int
            ID(s) of nodes to disconnect from this one, possibly empty.

        Note
        ----
        
        If any neighbor is not adjacent, ignore and continue.
        """
        for neigh_id in neighbor_ids:
            neigh = SimpleGraphNode.node_from_id[neigh_id]
            if neigh is not None:
                try:
                    self._adjacent.remove(neigh_id)
                    neigh._adjacent.remove(self._node_id)
                except KeyError:
                    pass # Node was not adjacent

######################### End of SimpleGraphNode class ###################

class Simple2DNode(SimpleGraphNode):
    """A SimpleGraphNode with additional 2D geometry.

    Parameters
    ----------
    
    x : int or float
        x-coordinate of the center
    y : int or float
        y-coordinate of the center
    r : nonnegative int or float
        bounding radius, defaults to Simple2DNode.default_radius
    """

    # This is the default bounding radius for newly-created nodes
    default_radius = 10
    
    INVALID_NODE_ID = SimpleGraphNode.INVALID_NODE_ID
    node_from_id = {INVALID_NODE_ID: None}

    def __init__(self, node_id, x, y, r = default_radius, **kwargs):
        SimpleGraphNode.__init__(self, node_id, **kwargs)
        Simple2DNode.node_from_id[node_id] = self
        self.x = x
        self.y = y
        if r >= 0:
            self.radius = r
        else:
            raise ValueError('Radius must be nonnegative; received %d' % r)

    def sq_distance_to(self, x, y):
        """The squared distance from this node's center to a given point."""
        return (x - self.x)**2 + (y - self.y)**2

    def covers_point(self, x, y):
        """Test whether a point is within this node's bounding radius."""
        distance = (x - self.x)**2 + (y - self.y)**2
        return (distance <= self.radius**2)

######################### End of Simple2DNode class ######################

from pygame.draw import circle as draw_circle
from pygame.draw import line as draw_line
from pygame import Color

class Simple2DGraph(object):
    """Graph container for Simple2DNode; for rendering with Pygame."""
    
    def __init__(self, surface, bg_color = None, node_color = None, edge_color = None):
        self.surface = surface
        (self.width, self. height) = surface.get_size()

        # Default colors for rendering
        if bg_color == None:
            bg_color = Color('#000000')
        if node_color == None:
            node_color = Color('#00bb00')
        if edge_color == None:
            edge_color = Color('#0000ee')
        self.colors = {'bg': bg_color,
                      'node': node_color,
                      'edge': edge_color
                      }
         
        # Nodes (and edges, since this uses SimpleGraphNode)
        self.node_ids = set()
        
    def add_node(self, node_id):
        """Add a node, using the node's ID."""
        if node_id != Simple2DNode.INVALID_NODE_ID:
            self.node_ids.add(node_id)
        
    def draw(self, dest):
        """Renders this graph onto the given surface."""

        node_color = self.colors['node']
        edge_color = self.colors['edge']
        node_info = []
        
        # Edge get drawn beneath the node, so they must all be done first
        for i in self.node_ids:
            node = Simple2DNode.node_from_id[i]
            center = (node.x, node.y)
            if node is not None:
                edge_width = node.radius // 2
                for neigh in node.get_neighbors():
                    draw_line(self.surface, edge_color, center, (neigh.x, neigh.y), edge_width)
            # Info for this node to be rendered later
            try:
                thiscolor = node.color
            except AttributeError:
                thiscolor = node_color
            node_info.append((thiscolor, center,node.radius))

        # Now draw all of the nodes (on top of the edges)
        for args in node_info:
            draw_circle(self.surface, *args)

        # And blit the entire graph to the destination surface
        dest.blit(self.surface, (0,0))
        
######################### End of Simple2DGraph class ######################        

class BFS_SimpleSearch(object):
    
    def __init__(self, start_id, target_id):
        if start_id == target_id:
            raise ValueError("Start_id == target_id == %d" % start_id)
        self.start_id = start_id
        self.target_id = target_id
        self.marked = [SimpleGraphNode.node_from_id[start_id]]
        self.index = 0
        targ = SimpleGraphNode.node_from_id[target_id]
        targ.color = pygame.Color('#ff0000')
        
    def visit_next(self):
        try:
            new_node = self.marked[self.index]
            new_node.color = pygame.Color('#ffffff')
        except IndexError:
            print("Target node ID %d was not found." % self.target_id)
            return None
        except TypeError:
            print("Target node ID %d has already been found!" % self.target_id)
            return [node.get_id() for node in self.marked]
        for node in new_node.get_neighbors():
            if node not in self.marked:
                if node.get_id() == self.target_id:
                    print('Target node %d was found.' % self.target_id)
                    self.index = None
                    return [node.get_id() for node in self.marked]
                else:
                    self.marked.append(node)
                    node.color = pygame.Color('#ee22ee')

        print([node.get_id() for node in self.marked[self.index:]])
        self.index = self.index + 1
        return [node.get_id() for node in self.marked]

if __name__=="__main__":
    print('Sample code for testing...click mouse to quit.')

    scr_w, scr_h = 640, 480
    pygame.init()
    screen = pygame.display.set_mode((scr_w, scr_h))

    v = [Simple2DNode(i,50+(i-1)*20, 20+(i-1)**2*30) for i in range(3)]
    v[0].connect_to(1,2)

    gsurf = pygame.Surface((scr_w, scr_h))
    g = Simple2DGraph(gsurf)
    for i in range(3):
        g.add_node(i)
        
    g.draw(screen)
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
    
