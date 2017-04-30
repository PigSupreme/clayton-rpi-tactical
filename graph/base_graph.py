#!/usr/bin/env python
"""
Module for various type of graph nodes/edges. WORK IN PROGRESS!
"""

INVALID_NODE_ID = -1
"""Any reference to this index is treated as being a nonexistant node."""

class BaseGraphNode(object):
    """Base class for various types of graph nodes.

    Parameters
    ----------
    node_id: int
        ID to assign this node, to allow consistency with external information.
    kwargs: any, optional
        Additional attributes can be set using keyword arguments. Each key 
        (except node_id) sets an instance variable with the same name. There is
        no error-checking in the base class, but subclasses may override this.
    
    Note
    ----
    Subclasses should call the base __init__() method (via super) to set the 
    node ID and any extra keyword arguments. The base class keeps a master
    directory of nodes by id, which can be accessed using the module function
    get_node(node_id). 
    """
    
    # This is used as a class variable, so that each node has a unique ID.
    _NEXT_ID = 0

    # This is the directory of nodes by index, without needing a manager.
    # To invalidate node n, use SimpleGraphNode.node_from_id[n] = None
    node_from_id = {INVALID_NODE_ID: None}

    def __init__(self, node_id, **kwargs):
        # Check if the requested ID is valid
        if node_id >= BaseGraphNode._NEXT_ID:
            self._node_id = node_id
            BaseGraphNode.node_from_id[node_id] = self
            BaseGraphNode._NEXT_ID = node_id + 1
            # self._adjacent = dict()
        else:
            raise ValueError('Node ID %d is already in use.' % node_id)
        # Set any extra information from keyword arguments
        for key in kwargs:
            if key is not 'node_id':
                setattr(self, key, kwargs[key])

def get_node(node_id):
    """A handle to the node with the given id; None for invalid nodes."""
    return BaseGraphNode.node_from_id[node_id]


class EasyGraphNode(BaseGraphNode):
    """A BaseGraphNode with anonymous directed edges.
    
    Adjacency is stored locally per node, using a dictionary keyed by node ID,
    Entries can then represent edge information (weight, label, etc.), but
    there is no way to access edges independently. To modify adjacency, use
    either the make_edges() or remove_edges() method on the source node.

    Parameters
    ----------
    node_id: int
        ID to assign this node, to allow consistency with external information.
    kwargs: any, optional
        Additional attributes can be set using keyword arguments. Each key 
        (except node_id) sets an instance variable with the same name.
    """
    
    def __init__(self, node_id, **kwargs):
        # Use the parent class to set id and additional information
        super(EasyGraphNode, self).__init__(node_id, **kwargs)
        
        # These use dictionaries for adjacency information
        self._adjacent = dict()


    def get_id(self):
        """Returns the ID of this node."""
        return self._node_id

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
        super(EasyGraphNode, self).node_from_id[self._node_id] = None

    def unignore_me(self):
        """Restore this node to being treated as active.

        Note
        ----
        After calling this, any information about this node (including edges
        to/from adjancent nodes) that existed before make_invalid() will once
        again be available.
        """
        super(EasyGraphNode, self).node_from_id[self._node_id] = self

    def make_edges(self, neighbor, label=1):
        """Create edge(s) from this node, with optional weight (default 1).

        Parameters
        ----------
        neighbor : int or list of int
            The ID of the node to connect to.
        label : object or list of objects, optional
            The label/weight information for the edge(s) (default = 1).
            If a single label is given, all neighbors get that label.
            If a list is given, it must have the same length as neighbor.

        Note
        ----
        This will overwrite any previous edge to the given neighbor(s).
        This does not check if neighbor(s) is/are currently active or valid,
        so we can create edges to node id's that do not yet exist.
        """
        # If neighbor is not a list, just make one edge.
        if not isinstance(neighbor, list):
            self._adjacent[neighbor] = label
            return

        # If label is not a list, all edges get the same label.
        if not isinstance(label, list):
            for node_id in neighbor:
                self._adjacent[node_id] = label
        # Otherwise, assign labels in the same order as neighbors are listed.
        else:
            if len(neighbor) != len(label):
                raise ValueError("Number of nodes (%d) does not match number of labels (%d)." % (len(neighbor), len(label)))
            for i in range(len(neighbor)):
                self._adjacent[neighbor[i]] = label[i]

    def remove_edges(self, neighbor):
        """Remove any existing edges to the given neighbor(s).

        Parameters
        ----------
        neighbor : int or list of int
            The ID of the nodes to remove edges to.
        """
        if not isinstance(neighbor, list):
            neighbor = [neighbor]

        for node_id in neighbor:
            try:
                del self._adjacent[node_id]
            except KeyError:
                pass # Ignore non-existant edges

    def neighbor_ids(self):
        """The set of IDs of active nodes adjacent to this one."""
        return {nid for nid in self._adjacent.keys() if get_node(nid) is not None}

    def neighbor_nodes(self):
        """The set of active nodes adjacent to this one."""
        nhood = {get_node(nid) for nid in self._adjacent.keys()}
        try:
            nhood.remove(None)
        except KeyError:
            pass
        return nhood

    def edges_from(self):
        """A dictionary of edges from this node, keyed by neighbor ID.
        Inactive neighbors are ignored.
        """
        result = dict()
        for node_id, label in self._adjacent.items():
            if get_node(node_id) is not None:
                result[node_id] = label
        return result

if __name__ == "__main__":
    import pygame

    # Pygame initiailzation
    pygame.init()
    screen = pygame.display.set_mode((640, 320))
    nodecolor = [(80+40*i, 20+40*i, 0) for i in range(4)]

    node = [EasyGraphNode(i, coords=(100+60*i*(i-2),70*(i+1))) for i in range(4)]
    node[0].make_edges([1,3],0)
    node[1].make_edges([0,1,2,3],1)
    node[2].make_edges([1,3],2)
    node[3].make_edges(1,3)
    node[1].remove_edges([0,1])

    for i in range(4):
        thisnode = get_node(i)
        if thisnode is not None:
            neighbors = thisnode.neighbor_ids()
            edges = thisnode.edges_from()
            xy = thisnode.coords
            print('Node %d has %d neighbors: %s' % (i,len(neighbors),neighbors))
            print('Edges with labels are: %s' % str(edges))
            pygame.draw.circle(screen,nodecolor[i],xy,5)
            for nid, edge_label in edges.items():
                wz = get_node(nid).coords
                pygame.draw.line(screen,nodecolor[i],xy,wz,3)

    pygame.display.update()

    while 1:

        try:
            for event in pygame.event.get():
                if event.type in [pygame.MOUSEBUTTONDOWN]:
                    pygame.quit()
        except pygame.error:
            pygame.quit()
