# -*- coding: utf-8 -*-
"""
Created on Sun Aug  2 14:54:21 2015

@author: lothar
"""

class GraphNode(object):
    """Base class for graph nodes/vertices."""

    INVALID_NODE_ID = -1
    """Any reference to this index is treated as being a nonexistant node."""
    
    # This is used by the manager so that each node has a unique ID. 
    _NEXT_NODE_ID = 0
    
    # This is the directory of nodes by index, without needing a manager.
    # To invalidate node n, use GraphNode.node_by_id[n] = None
    node_by_id = {INVALID_NODE_ID: None}
    
    def __init__(self, node_id, **kwargs):
        """Creates a graph node, sets its ID and any extra information.

        Note
        ----
        Functions that modify adjacency/incidence must update the private
        attributes _adjacent and _incident as appropriate.
        """
        if node_id >= GraphNode._NEXT_NODE_ID:
            self._node_id = node_id
            GraphNode.node_by_id[node_id] = self
            GraphNode._NEXT_NODE_ID = node_id + 1
            self._adjacent = dict() # Adjacent nodes, keyed by node ID.
            self._incident = dict() # Incident edges, keyed by edge ID.
        else:
            raise ValueError('Node ID %d is already in use.' % node_id)
        # Set any extra information
        for key in kwargs:
            self.key = kwargs[key]
            
    def get_id(self):
        """Returns the ID of this node (TODO: Modify to use getattr)."""
        return self_id
            
    def connect_to_node(self, neighbor_id, edge_id=None, directed=False, reverse_id=None):
        """Connect to another node, optionally using a given edge.
        
        Parameters
        ----------
        neighbor_id : int
            The node to connect to.
        edge_id : int
            The edge to connect with. If not given, a new edge is created.
        directed : bool
            If set to True, make a directed (one-way) connection only.
        reverse_id : int
            If directed is False; the edge to connect back to this node.
            
        
        Returns
        -------
        bool : True if the connection was successful, False otherwise.
        
        Raises
        ------
        ValueError: If edge_id or reverse_id are specified, but have a node_id
        that is inconsistent with the node_id's given to this function.

        """
        if GraphNode.node_by_id(neighbor_id) is None:
            return False
            
        # Check if we have a valid edge. If not, create one:
        if edge_id is None
            use_edge = GraphEdge(self._node_id, neighbor_id)
        else:                        
        # Check that the given edge is valid, and has the correct nodes:
        use_edge = GraphEdge.edge_by_id(edge_id)
        if use_edge is None:
            raise ValueError('Edge ID %d is currently invalid' % edge_id)
        else:
            # TODO: Check the source/destination nodes
            pass
        
        
        # Now connect to the neighbor:
        self._adjacent[neighbor_id] = use_edge
        self._incident[use_edge] = neighbor_id
        
        # If this is not a directed edge, connect backwards; this is done by
        # connect_to_node() on the neighbor node, with directed=True.
        if not directed:
            GraphNode.node_by_id(neighbor_id).connect_to_node(self._node_id, reverse_id, True)
    
    
