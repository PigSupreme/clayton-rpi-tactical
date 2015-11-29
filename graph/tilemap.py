# -*- coding: utf-8 -*-
"""
Created on Sat Nov 28 17:17:34 2015

@author: lothar
"""

from random import randint
from base_graph_simple import Simple2DNode, Simple2DGraph, SimpleGraphNode
from base_graph_simple import BFS_SimpleSearch

import pygame

class MazeTile(object):
    """Four-directional room/corridor."""

    # Types of tiles
    DEADEND, PASSAGE, TEE, CROSS = range(4)
    MAX_TYPE = 3
    # Exits: [EAST, NORTH, WEST, SOUTH]
    default_exits = {DEADEND: [1,0,0,0],
            PASSAGE: [1,0,1,0],
            TEE: [1,1,1,0],
            CROSS: [1,1,1,1]}

    def __init__(self, tile_type = None, rotation = 0):
        if tile_type == None:
            tile_type = randint(0,MazeTile.MAX_TYPE)
        exits = MazeTile.default_exits[tile_type]
        rotation = rotation % 4
        if rotation == 0:
            self.exits = exits
        else:
            self.exits = exits[-rotation:] + exits[:-rotation]
            
    def rotate(self, rotation = 1):
        rotation = rotation % 4
        if rotation > 0:
            self.exits = self.exits[-rotation:] + self.exits[:-rotation]

class TileMaze2DGraph(Simple2DGraph):
    """Four-directional tile maze."""
    
    def __init__(self, rows, cols, surface):
        # For now, we just make a random maze of the given size.
        print("Generating random maze...")
        Simple2DGraph.__init__(self, surface)
        self.mazedata = []
        for i in range(rows):
            row = []
            for j in range(cols):
                row.append(MazeTile(randint(1,3),randint(0,3)))
            self.mazedata.append(row)
        print("...maze complete.")

        # Convert maze data into a graph
        self.make_Simple2DNodes(surface)
        self.update_edges()
        print("...surface graph complete.")
        
    def make_Simple2DNodes(self, surface):
        """Creates the graph nodes for this maze."""
        width, height = surface.get_size()
        maze = self.mazedata
        rows = len(maze)
        cols = len(maze[0])
        dx = width // (1+cols)
        dy = height // (1+rows)
        self.surface = surface
        #self.graph = Simple2DGraph(surface)
    
        # Add the nodes to the graph
        self.node_array = []
        nid = 0
        for i in range(rows):
            row = []
            for j in range(cols):
                node = Simple2DNode(nid, (j+1)*dx, (i+1)*dy, 8)
                row.append(node)
                self.add_node(nid)
                nid = nid + 1
            self.node_array.append(row)
            
        # Update instance variables and exit
        self.width, self.height = width, height
        self.rows, self.cols = rows, cols
        self.dx, self.dy = dx, dy
    
    def node_at(self, row, col):
        return self.node_array[row][col]
        
    def tile_at(self, row, col):
        return self.mazedata[row][col]

    def nearest_node(self, x, y):
        return (x - self.dx/2) // self.dx, (y-self.dy/2) // self.dy
    
    def update_edges(self):
        """Update graph edges based on underlying maze data."""
        maze = self.mazedata        
        
        def node_id(row, col):
            return row*self.cols + col
    
        # Check for vertical edges
        for i in range(self.rows - 1):
            for j in range(self.cols):
                node = Simple2DNode.node_from_id[node_id(i,j)]
                if maze[i][j].exits[3] and maze[i+1][j].exits[1]:
                    node.connect_to(node_id(i+1,j))
                else:
                    node.disconnect_from(node_id(i+1,j))
    
        # Check for horizontal edges
        for j in range(self.cols - 1):
            for i in range(self.rows):
                node = Simple2DNode.node_from_id[node_id(i,j)]
                if maze[i][j].exits[0] and maze[i][j+1].exits[2]:
                    node.connect_to(node_id(i,j+1))
                else:
                    node.disconnect_from(node_id(i,j+1))
                     
    def draw_tiles(self):
        """Draw tiles and exits for this maze, but no graph connections."""
        width, height = self.surface.get_size()
        node_color = pygame.Color('#ffffff')
        edge_color = pygame.Color('#ff4444')
        radius = 10
        spoke = 15
        for i in range(self.rows):
            for j in range(self.cols):
                center_x = (j+1)*self.dx
                center_y = (i+1)*self.dy
                center = (center_x, center_y)
                pygame.draw.circle(self.surface, node_color, center, radius)
                if self.mazedata[i][j].exits[0] == 1:
                    pygame.draw.line(self.surface, edge_color, center, (center_x + spoke, center_y),8)
                if self.mazedata[i][j].exits[1] == 1:
                    pygame.draw.line(self.surface, edge_color, center, (center_x, center_y - spoke),8)
                if self.mazedata[i][j].exits[2] == 1:
                    pygame.draw.line(self.surface, edge_color, center, (center_x - spoke, center_y),8)
                if self.mazedata[i][j].exits[3] == 1:
                    pygame.draw.line(self.surface, edge_color, center, (center_x, center_y + spoke),8)

    def draw_graph(self):
        """Draw connecting corridors for this maze."""
        self.draw(self.surface)


class bfs_search(object):
    
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
            
        for node in new_node.get_neighbors():
            if node not in self.marked:
                if node.get_id() == self.target_id:
                    print('Target node %d was found.' % self.target_id)
                    self.index = -1
                    return [node.get_id() for node in self.marked]
                else:
                    self.marked.append(node)
                    node.color = pygame.Color('#ee22ee')

        print([node.get_id() for node in self.marked[self.index:]])
        self.index = self.index + 1
        return [node.get_id() for node in self.marked]

                
            

if __name__=="__main__":
    import pygame
    
    mrow, mcol = 8, 12
    screen = pygame.display.set_mode((640,400))
    a = TileMaze2DGraph(mrow,mcol,screen)
    a.draw_tiles()
    a.draw_graph()
    pygame.display.update()
    
    print "Testing code...right-click to exit."
    search = BFS_SimpleSearch(0,15)

    b_done = False
    while not b_done:
        try:
            for event in pygame.event.get():
                if event.type in [pygame.MOUSEBUTTONDOWN]:
                    if event.button == 3:
                        b_done = True
                        break
                    try:
                        col, row = a.nearest_node(*event.pos)
                        #a.tile_at(row, col).rotate()
                        b = search.visit_next()
                        screen.fill(pygame.Color(0,0,0))
                        a.update_edges()
                        a.draw_tiles()
                        a.draw_graph()
                        pygame.display.update()
                    except IndexError:
                        pass
                    
        except pygame.error:
            b_done = True
    
    pygame.quit()
