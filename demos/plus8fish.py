#!/usr/bin/env python
"""Plus8 fish FSM demo"""

# for python3 compat
from __future__ import unicode_literals
from __future__ import absolute_import
from __future__ import print_function
from __future__ import division

import sys, pygame

from pygame.locals import QUIT, MOUSEBUTTONDOWN

import logging
logging.basicConfig(format='%(levelname)s: %(message)s', level=logging.WARN)

from random import randint, shuffle, choice

sys.path.extend(['..','../vehicle'])
import steering
# Override some default values from steering_constants:
steering.FLOCKING_RADIUS_MULTIPLIER = 3.0
steering.FLOCKING_SEPARATE_SCALE = 1.4

UPDATE_SPEED = 0.2
OBS_RADIUS = 350
OBSTACLE_COUNT = 16

FISH_RADIUS = 25
FISH_COUNT = 18
FOOD_COUNT = 10

SHARK_RADIUS = 60

SCREENSIZE = (1200, 800)

INF = float('inf')

# Note: Adjust this depending on where this file ends up.
sys.path.append('..')
from vpoints.point2d import Point2d

from vehicle.vehicle2d import load_pygame_image
from vehicle.vehicle2d import SimpleVehicle2d, SimpleObstacle2d, BaseWall2d
ZERO_VECTOR = Point2d(0,0)

import fsm_ex.ent_fish as entfish
import fsm_ex.ent_shark as entshark

class FishFeeder(pygame.sprite.Group):
    """Mangager object for keeping track of fish food."""

    def __init__(self, obstacles, maxfood, foodsprite_data):
        super(self.__class__, self).__init__()
        self.obs = obstacles
        self.maxfood = maxfood
        self.spritedata = foodsprite_data
        # Generate pygame sprites for food

    def add_food(self, num_new=1):
        """Adds food unit(s), but don't exceed the maximum number."""
        while num_new > 0 and len(self) <= self.maxfood:
            # Generate a new unit of food
            new_pos = Point2d(randint(30, sc_width-30), randint(30, sc_height-30))
            new_food = SimpleObstacle2d(new_pos, 2.5, self.spritedata)
            #new_food.sprite.rect.center = new_pos
            # If it doesn't collide with any fish/obstacles, add to our sprite group
            if pygame.sprite.spritecollideany(new_food.sprite, self, pygame.sprite.collide_circle):
                del new_food
            else:
                new_food.sprite.add(self, allsprites)
                num_new -= 1
                logging.debug('Fishfeeder added food at %s. %d left' % (new_pos, num_new))

    def random_food_pos(self):
        if self.sprites():
            return Point2d(*choice(self.sprites()).rect.center)
        else:
            return None

    def nearest_food_pos(self, location):
        result = None
        dsq = INF
        for food in self.sprites():
           food_loc = Point2d(*food.rect.center)
           food_dsq = (location - food_loc).sqnorm()
           if food_dsq < dsq:
               result = food_loc
               dsq = food_dsq
        return result

    def chomp(self, fish):
        foodhit = pygame.sprite.spritecollideany(fish.sprite, self, pygame.sprite.collide_circle)
        if foodhit is not None:
            # foodhit is the sprite that was collided with
            logging.info('Eating food at {!s}'.format(foodhit.rect.center))
            foodhit.kill()
            del(foodhit)
            self.add_food()
            return True
        else:
            return False

if __name__ == "__main__":
    pygame.init()

    # Display constants
    size = sc_width, sc_height = SCREENSIZE
    screen = pygame.display.set_mode(size)
    pygame.display.set_caption('Fish FSM demo')
    bgcolor = 111, 145, 192

    # Number of vehicles and obstacles
    numfish = FISH_COUNT
    numshark = 1
    numveh = numfish + numshark
    numobs = OBSTACLE_COUNT
    total = 2*numveh+numobs

    # Load vehicle images
    fish_img, fish_rec = load_pygame_image('../images/gpig.png', -1)
    shark_img, shark_rec = load_pygame_image('../images/rpig.png', -1)

    # Food sprite images (generated here)
    food_img = pygame.Surface((5,5))
    food_rect = food_img.get_rect()
    foodsprite_data = (food_img, food_rect)

    # Static obstacle image (shared among all obstacles)
    obs_img, obs_rec = load_pygame_image('../images/circle.png', -1)

    # Randomly generate initial placement for vehicles
    pos = [Point2d(randint(50, sc_width-50), randint(50, sc_height-50)) for i in range(numveh)]
    pos[0] = Point2d(sc_width/2, sc_height/2)
    vel = Point2d(20,0)

    # Array of vehicles with associated spritedata
    obj = []
    # Fish...
    for i in range(numfish):
        fish = entfish.Plus8Fish(i, FISH_RADIUS, pos[i], Point2d(0,0), (fish_img, fish_rec))
        obj.append(fish)

    # ...and Sharks!
    for i in range(numfish,numveh):
        fish = entshark.Plus8Shark(i, SHARK_RADIUS, pos[i], Point2d(0,0), (shark_img, shark_rec))
        obj.append(fish)

    # Lists of vehicles for later use
    fishlist = obj[:numfish]
    sharklist = obj[numfish:numfish+numshark]
    vehicles = obj[:]

    # Static obstacles for pygame (randomly-generated positions)
    yoffset = sc_height//(numobs+1)
    yvals = list(range(yoffset, sc_height-yoffset, yoffset))
    shuffle(yvals)
    for i in range(2*numveh, 2*numveh + numobs):
        offset = (i+1.0-2*numveh)/(numobs+1)
        rany = yvals[i-2*numveh]
        new_pos = Point2d(offset*sc_width, rany)
        obstacle = SimpleObstacle2d(new_pos, OBS_RADIUS, (obs_img, obs_rec))
        obj.append(obstacle)

    # This gives a convenient list of (non-wall) obstacles for later use
    obslist = obj[numveh:]

    # Static Walls for pygame (screen border only)
    wall_list = (BaseWall2d((sc_width//2, 5), sc_width-5, 5, Point2d(0,1)),
                 BaseWall2d((sc_width//2, sc_height-5), sc_width-5, 5, Point2d(0,-1)),
                 BaseWall2d((5, sc_height//2), sc_height-5, 5, Point2d(1,0)),
                 BaseWall2d((sc_width-5,sc_height//2), sc_height-5, 5, Point2d(-1,0)))
    obj.extend(wall_list)

    # Set-up pygame rendering
    rendergroup = [thing.sprite for thing in obj]
    allsprites = pygame.sprite.RenderPlain(rendergroup)

    # Food manager (needs allsprites for some reason)
    feeder = FishFeeder(obslist, FOOD_COUNT, foodsprite_data)
    feeder.add_food(FOOD_COUNT)

    # Environment info for each fish...
    # ...only works for a single shark
    for fish in fishlist:
        fish.UPDATE_SPEED = UPDATE_SPEED
        fish.obs = obslist
        fish.walls = wall_list
        fish.feeder = feeder
        fish.steering.set_target(SEPARATE=fishlist[:]+sharklist[:], ALIGN=fishlist[:], COHESION=fishlist[:])
        fish.shark = sharklist[0]  # This assumes a single shark
    #...and for each shark
    for fish in sharklist:
        fish.UPDATE_SPEED = UPDATE_SPEED
        fish.obs = obslist
        fish.walls = wall_list
        fish.prey = fishlist

    # Used by pygame for collision detection
    COLLIDE_FUNCTION = pygame.sprite.collide_circle

    ### Main loop ###
    while True:
        for event in pygame.event.get():
            if event.type in [QUIT, MOUSEBUTTONDOWN]:
                pygame.quit()
                sys.exit()

        # FSM Updates (which update movement and steering)
        for veh in vehicles:
            veh.fsm.update()

        # Update Sprites (via pygame sprite group update)
        allsprites.update(UPDATE_SPEED)

        #pygame.time.delay(2)

        # Screen update; inefficient!
        screen.fill(bgcolor)
        allsprites.draw(screen)
        feeder.draw(screen)
        pygame.display.flip()

    pygame.time.delay(2000)










