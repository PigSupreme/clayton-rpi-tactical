# -*- coding: utf-8 -*-
"""
Created on Sat Nov 28 17:17:34 2015

@author: lothar
"""

mrow, mcol = 4, 5

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

def make_random_maze(rows, cols):
    maze = []
    for i in range(rows):
        row = []
        for j in range(cols):
            row.append(MazeTile(randint(0,3),randint(0,3)))
        maze.append(row)
    return maze


def draw_maze(maze, surface):
    width, height = surface.get_size()
    node_color = pygame.Color('#ffffff')
    edge_color = pygame.Color('#ff4444')
    radius = 10
    spoke = 20
    rows = len(maze)
    cols = len(maze[0])
    dx = width // (1+cols)
    dy = height // (1+rows)
    for i in range(rows):
        for j in range(cols):
            center_x = (j+1)*dx
            center_y = (i+1)*dy
            center = (center_x, center_y)
            pygame.draw.circle(surface, node_color, center, radius)
            if maze[i][j].exits[0] == 1:
                pygame.draw.line(surface, edge_color, center, (center_x + spoke, center_y),8)
            if maze[i][j].exits[1] == 1:
                pygame.draw.line(surface, edge_color, center, (center_x, center_y - spoke),8)
            if maze[i][j].exits[2] == 1:
                pygame.draw.line(surface, edge_color, center, (center_x - spoke, center_y),8)
            if maze[i][j].exits[3] == 1:
                pygame.draw.line(surface, edge_color, center, (center_x, center_y + spoke),8)

def make_mazegraph(maze, surface):
    width, height = surface.get_size()
    rows = len(maze)
    cols = len(maze[0])
    dx = width // (1+cols)
    dy = height // (1+rows)
    mg = Simple2DGraph(surface)

    # First pass adds the nodes to the graph
    nid = 0
    for i in range(rows):
        for j in range(cols):
            node = Simple2DNode(nid, (j+1)*dx, (i+1)*dy, 8)
            mg.add_node(nid)
            nid = nid + 1

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

    mg.draw(surface)

if __name__=="__main__":
    a = make_random_maze(4,5)
    screen = pygame.display.set_mode((640,480))
    draw_maze(a,screen)
    make_mazegraph(a,screen)
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