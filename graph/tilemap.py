# -*- coding: utf-8 -*-
"""
Created on Sat Nov 28 17:17:34 2015

@author: lothar
"""

from random import randint
from base_graph_simple import Simple2DNode, Simple2DGraph


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
            self.exits = exits[:-rotation] + exits[:rotation]

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
                row.append(MazeTile(randint(0,3),randint(0,3)))
            self.mazedata.append(row)
        print("...maze complete.")

        # Convert maze data into a graph
        self.make_Simple2Dgraph(surface)
        print("...surface graph complete.")
        
    def make_Simple2Dgraph(self, surface):
        width, height = surface.get_size()
        maze = self.mazedata
        rows = len(maze)
        cols = len(maze[0])
        dx = width // (1+cols)
        dy = height // (1+rows)
        self.surface = surface
        #self.graph = Simple2DGraph(surface)
    
        # First pass adds the nodes to the graph
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
    
        def node_id(row, col):
            return row*cols + col
    
        # Check for vertical edges
        for i in range(rows - 1):
            for j in range(cols):
                if maze[i][j].exits[3] and maze[i+1][j].exits[1]:
                    Simple2DNode.node_from_id[node_id(i,j)].connect_to(node_id(i+1,j))
    
        # Check for horizontal edges
        for j in range(cols - 1):
            for i in range(rows):
                if maze[i][j].exits[0] and maze[i][j+1].exits[2]:
                    Simple2DNode.node_from_id[node_id(i,j)].connect_to(node_id(i,j+1))
                    
        # Update instance variables and exit
        self.width, self.height = width, height
        self.rows, self.cols = rows, cols
        self.dx, self.dy = dx, dy
    
    def draw_maze(self):
        width, height = self.surface.get_size()
        node_color = pygame.Color('#ffffff')
        edge_color = pygame.Color('#ff4444')
        radius = 10
        spoke = 20
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
        self.draw(self.surface)

if __name__=="__main__":
    mrow, mcol = 6, 8
    screen = pygame.display.set_mode((640,480))
    a = TileMaze2DGraph(mrow,mcol,screen)
    a.draw_graph()
    a.draw_maze()
    pygame.display.update()
    
    print "Testing code...click mouse to exit."
    while 1:
        try:
            for event in pygame.event.get():
                if event.type in [pygame.MOUSEBUTTONDOWN]:
                    pygame.quit()
                    break
        except pygame.error:
            pygame.quit()
            break