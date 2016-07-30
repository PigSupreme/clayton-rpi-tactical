
#!/usr/bin/env python
"""Non-flocking vehicle demo."""

# for python3 compat
from __future__ import unicode_literals
from __future__ import absolute_import
from __future__ import print_function
from __future__ import division

import sys, pygame
from pygame.locals import QUIT, MOUSEBUTTONDOWN
from random import randint, shuffle

TARGET_FREQ = 2000
UPDATE_SPEED = 0.2

INF = float('inf')

# Note: Adjust this depending on where this file ends up.
sys.path.append('..')
from vpoints.point2d import Point2d

from vehicle.vehicle2d import load_pygame_image
from vehicle.vehicle2d import SimpleVehicle2d, SimpleObstacle2d, BaseWall2d
ZERO_VECTOR = Point2d(0,0)

from fsm_ex.state_machine import State, StateMachine

class InitialState(State):
    
    def execute(self, agent):
        print('Inital state: Vehicle %d' % agent.ent_id)
        agent.steering.set_target(AVOID=obslist, WALLAVOID=[30, wall_list])
        agent.fsm.change_state(WanderState())


class SeekingState(State):
    """Vehicle is currently moving towards a given point."""

    def enter(self, agent):
        # Set target; estimate time to reach it
        goal_pos = (agent.goal.pos[0], agent.goal.pos[1])
        goal_dist = (agent.pos - agent.goal.pos).norm()
        est_time = goal_dist / agent.maxspeed
        agent.seek_countdown = est_time * 1.5 / UPDATE_SPEED
        
        # Highest-numbered vehicle (GREEN) uses SEEK
        if agent.ent_id == numveh-1:
            agent.steering.set_target(SEEK=goal_pos)
        else:
            # All others use ARRIVE            
            agent.steering.set_target(ARRIVE=goal_pos)

    def execute(self, agent):
        # If we take too long to reach target, switch to wandering
        counter = agent.seek_countdown - 1.0
        if counter < 0:
            agent.fsm.change_state(WanderState())
        else:
            agent.seek_countdown = counter
        
    def on_msg(self, agent, message):
        if message == 'MSG_ARRIVED':
            agent_id = agent.ent_id
            print('Vehicle %d: Received MSG_ARRIVED' % agent_id)
            agent.fsm.change_state(WaitingState())
            return True
        else:
            return False


class WaitingState(State):
    
    def enter(self, agent):
        agent.wait_timer = TARGET_FREQ // 2
    
    def execute(self, agent):
        agent.wait_timer = agent.wait_timer - 1
        if agent.wait_timer <= 0:
            del agent.wait_timer
            agent.fsm.change_state(WanderState())
            
    def leave(self, agent):
        """Code to execute just before changing from this state."""
        # Turn off steering behaviour (SEEK or ARRIVE)
        agent.steering.deactivate_behaviour('SEEK')
        agent.steering.deactivate_behaviour('ARRIVE')
        

class WanderState(State):
    """Vehicle will WANDER until it receives new instructions."""
    
    def enter(self, agent):
        agent.steering.set_target(WANDER=(250, 10, 3))
        
    def leave(self, agent):
        agent.steering.deactivate_behaviour('WANDER')
        
    def on_msg(self, agent, message):
        if message == 'MSG_AWAKEN':
            agent_id = agent.ent_id
            print('Vehicle %d: Received MSG_AWAKEN' % agent_id)
            agent.fsm.change_state(SeekingState())
            return True
        else:
            return False
            

if __name__ == "__main__":
    pygame.init()

    # Display constants
    size = sc_width, sc_height = 800, 640
    screen = pygame.display.set_mode(size)
    pygame.display.set_caption('FSM demo with SEEK - ARRIVE - WANDER and Pygame collisions')
    bgcolor = 111, 145, 192
    
    # Number of vehicles and obstacles
    numveh = 3
    numobs = 16
    total = 2*numveh+numobs

    # Sprite images and pygame rectangles
    img = list(range(total))
    rec = list(range(total))

    # Load vehicle images
    img[0], rec[0] = load_pygame_image('../images/rpig.png', -1)
    img[1], rec[1] = load_pygame_image('../images/ypig.png', -1)
    img[2], rec[2] = load_pygame_image('../images/gpig.png', -1)

    # Steering behaviour target images (generated here)
    for i in range(numveh, 2*numveh):
        img[i] = pygame.Surface((5,5))
        rec[i] = img[i].get_rect()

    # Static obstacle image (shared among all obstacles)
    obs_img, obs_rec = load_pygame_image('../images/circle.png', -1)
    for i in range(2*numveh, 2*numveh + numobs):
        img[i], rec[i] = obs_img, obs_rec

    # Randomly generate initial placement for vehicles
    pos = [Point2d(randint(30, sc_width-30), randint(30, sc_height-30)) for i in range(numveh)]
    pos[0] = Point2d(sc_width/2, sc_height/2)
    vel = Point2d(20,0)

    # Array of vehicles and associated pygame sprites
    obj = list(range(numveh))
    for i in range(numveh):
        obj[i] = SimpleVehicle2d(pos[i], 50, vel, (img[i], rec[i]))
        obj[i].ent_id = i
    rgroup = [veh.sprite for veh in obj]
    vehicles = obj[:]

    # Steering behaviour targets (implemented as vehicles for later use...)
    for i in range(numveh, 2*numveh):
        x_new = randint(30, sc_width-30)
        y_new = randint(30, sc_height-30)
        new_pos = Point2d(x_new,y_new)
        target = SimpleVehicle2d(new_pos, 10, ZERO_VECTOR, (img[i], rec[i]))
        obj.append(target)
        rgroup.append(target.sprite)

    # Static obstacles for pygame (randomly-generated positions)
    yoffset = sc_height//(numobs+1)
    yvals = list(range(yoffset, sc_height-yoffset, yoffset))
    shuffle(yvals)
    for i in range(2*numveh, 2*numveh + numobs):
        offset = (i+1.0-2*numveh)/(numobs+1)
        rany = yvals[i-2*numveh]
        new_pos = Point2d(offset*sc_width, rany)
        obstacle = SimpleObstacle2d(new_pos, 10, (img[i], rec[i]))
        obj.append(obstacle)
        rgroup.append(obstacle.sprite)
    # This gives a convenient list of (non-wall) obstacles for later use
    obslist = obj[2*numveh:]

    # Static Walls for pygame (screen border only)
    wall_list = (BaseWall2d((sc_width//2, 10), sc_width-20, 4, Point2d(0,1)),
                 BaseWall2d((sc_width//2, sc_height-10), sc_width-20, 4, Point2d(0,-1)),
                 BaseWall2d((10, sc_height//2), sc_height-20, 4, Point2d(1,0)),
                 BaseWall2d((sc_width-10,sc_height//2), sc_height-20, 4, Point2d(-1,0)))
    obj.extend(wall_list)
    for wall in wall_list:
        rgroup.append(wall.sprite)

    # Set-up pygame rendering
    allsprites = pygame.sprite.RenderPlain(rgroup)

    ### Vehicle steering targets ###
    # Big red (ARRIVE, medium hesitance set by FSM later)
    x_new, y_new = obj[3].pos[0], obj[3].pos[1]
    obj[0].goal = obj[3]

    # Yellow (ARRIVE, low hesitance set by FSM later)
    x_new, y_new = obj[4].pos[0], obj[4].pos[1]
    obj[1].goal = obj[4]

    # Green (SEEK set by FSM later)
    x_new, y_new = obj[5].pos[0], obj[5].pos[1]
    obj[2].goal = obj[5]

    # Target sprite groups for each vehicle
    for i in range(numveh):
        obj[i].tgroup = pygame.sprite.GroupSingle(obj[i + numveh].sprite)

    # Give each vehicle its own FSM
    for i in range(numveh):
        fsm = StateMachine(obj[i])
        fsm.set_state(InitialState())
        obj[i].fsm = fsm

    # Used by pygame for collision detection
    COLLIDE_FUNCTION = pygame.sprite.collide_circle

    ### Main loop ###
    ticks = 0
    while 1:
        for event in pygame.event.get():
            if event.type in [QUIT, MOUSEBUTTONDOWN]:
                pygame.quit()
                sys.exit()

        # Update Vehicles (via manually calling each move() method)
        for v in vehicles:
            v_id = v.ent_id
            v.move(UPDATE_SPEED)
            hit_list = pygame.sprite.spritecollide(v.sprite, v.tgroup, False, COLLIDE_FUNCTION)
            if len(hit_list) > 0:
                v.tgroup.remove(obj[v_id + numveh].sprite)
                v.fsm.handle_msg('MSG_ARRIVED')

        # FSM Updates
        for i in range(numveh):
            obj[i].fsm.update()

        # Update steering targets every so often
        ticks += 1
        if ticks == TARGET_FREQ:
            print('Updating targets!')
            for i in range(numveh):
                x_new = randint(30, sc_width-30)
                y_new = randint(30, sc_height-30)
                new_pos = Point2d(x_new,y_new)
                obj[i + numveh].pos = new_pos
                obj[i].fsm.handle_msg('MSG_AWAKEN')
                obj[i].tgroup.add(obj[i + numveh].sprite)
                ticks = 0

        # Update Sprites (via pygame sprite group update)
        allsprites.update(UPDATE_SPEED)

        #pygame.time.delay(2)

        # Screen update; inefficient!
        screen.fill(bgcolor)
        allsprites.draw(screen)
        pygame.display.flip()

    pygame.time.delay(2000)
