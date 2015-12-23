# -*- coding: utf-8 -*-
"""Module containing BOID steering behavior functions.

Since we typically won't need every single behaviour for a given instance,
import the needed ones from this module. The function that returns the force
for a given behaviour is named force_name-of-behviour.
"""

from sys import path
path.insert(0, '../vpoints')
from point2d import Point2d
INF = float('inf')
from math import sqrt

# This contols the gradual deceleration for ARRIVE behavior.
# Larger values will cause more gradual deceleration
ARRIVE_DECEL_TWEAK = 10.0

# Used by EVADE; we ignore the predator if it is too far away.
EVADE_PANIC_SQ = 160**2

# This controls the size of an object detection box for AVOID obstacles
# Length in front of vehicle is 100%-200% of this
AVOID_MIN_LENGTH = 25.0
# Tweaking constant for braking force of AVOID obstacles
AVOID_BRAKE_WEIGHT = 2.0


# Random number generator
from random import Random
rand_gen = Random()
rand_gen.seed()
rand_uni = lambda x: rand_gen.uniform(-x, x)


def force_seek(owner, target):
    """Steering force for SEEK behaviour.

    This is a simple behaviour that directs the owner towards a given point.
    Other, more complex behaviours make use of this.

    Parameters
    ----------
    owner: Vehicle
        The vehicle computing this force.
    position: Point2d
        The target point that owner is seeking to.
    """
    targetvel = (target - owner.pos).unit()
    targetvel = targetvel.scale(owner.maxspeed)
    return targetvel - owner.vel

def force_flee(owner, target, panic_squared=INF):
    """Steering force for FLEE behaviour.

    Another simple behaviour that directs the owner away from a given point.

    Parameters
    ----------
    owner: Vehicle
        The vehicle computing this force.
    position: Point2d
        The target point that owner is fleeing from.
    panic_squared: float
        If specified, only compute a flee_force if squared distance
        to the target is less than this value.
    """
    targetvel = (owner.pos - target)
    if 1 < targetvel.sqnorm() < panic_squared:
        targetvel = targetvel.unit().scale(owner.maxspeed)
        return targetvel - owner.vel
    else:
        return Point2d(0,0)

def force_arrive(owner, target, hesitance=2.0):
    """Steering force for ARRIVE behaviour.

    This works like SEEK, except the vehicle gradually deccelerates as it
    nears the target position. The optional third parameter controls the
    amount of decceleration.

    Parameters
    ----------
    owner: Vehicle
        The vehicle computing this force.
    position: Point2d
        The target point that owner is to arrive at.
    hesistance: float
        Controls the time it takes to deccelerate; higher values give more
        gradual (and slow) decceleration. Suggested values are 1.0 - 10.0.

    """
    target_offset = (target - owner.pos)
    dist = target_offset.norm()
    if dist > 0:
        # The constant on the next line may need tweaking
        speed = dist / (ARRIVE_DECEL_TWEAK * hesitance)
        if speed > owner.maxspeed:
            speed = owner.maxspeed
        targetvel = target_offset.scale(speed/dist)
        return targetvel - owner.vel
    else:
        return Point2d(0,0)

def force_pursue(owner, prey):
    """Steering force for PURSUE behaviour.

    Similar to SEEK, but lead the prey by estimating its future location,
    based on current velocities.

    Parameters
    ----------
    owner: Vehicle
        The vehicle computing this force.
    prey: Vehicle
        The vehicle that owner will pursue.
    """
    prey_offset = prey.pos - owner.pos
    # If prey is in front and moving our way, SEEK to prey's position
    # Compute this using dot products; constant below is cos(10 degrees)
    if prey_offset * prey.vel < -0.966:
        return force_seek(owner, prey.pos)

    # Otherwise, predict the future position of prey, assuming it has a
    # constant velocity. Prediction time is the distance to prey, divided
    # by the sum of our max speed and prey's current speed.
    ptime = prey_offset.norm()/(owner.maxspeed + prey.vel.norm())
    return force_seek(owner, prey.vel.scale(ptime) + prey.pos)

def force_evade(owner, predator):
    """Steering force for EVADE behaviour.

    Similar to FLEE, but try to get away from the predicted future position
    of the predator. Predators far away are ignored, EVADE_PANIC_SQ is used
    to control the panic distance passed to FLEE.

    Parameters
    ----------
    owner: Vehicle
        The vehicle computing this force.
    predator: Vehicle
        The vehicle that owner will pursue.
    """
    predator_offset = predator.pos - owner.pos
    # Predict the future position of predator, assuming it has a constant
    # velocity. Prediction time is the distance to predator divided
    # by the sum of our max speed and predator's current speed.
    ptime = predator_offset.norm()/(owner.maxspeed + predator.vel.norm())
    return force_flee(owner, predator.vel.scale(ptime) + predator.pos, EVADE_PANIC_SQ)

def force_wander(steering):
    """Steering force for WANDER behavior.

    Parameters
    ----------
    steering: SteeringBehavior
        An instance of SteeringBehavior (*not* a Vehicle, see note below)

    Note
    ----
    WANDER requires persistant data (specifically, the target of the wander
    circle), so we need access to the SteeringBehavior itself instead of the
    vehicle that owns it.
    """
    owner = steering.vehicle
    target, dist, rad, jitter = steering.targets['WANDER']

    # Add a random displacement to previous target and reproject
    target += Point2d(rand_uni(jitter), rand_uni(jitter))
    target.normalize()
    target = target.scale(rad)
    steering.targets['WANDER'][0] = target
    return force_seek(owner, owner.pos + target + owner.front.scale(dist))

def force_avoid(owner, obs_list):
    """Steering force for AVOID stationary obstacles behaviour.

    This projects a box in front of the owner and tries to find an obstacle
    for which collision is imminent (not always the closest obstacle). The
    owner will attempt to steer around that obstacle.

    Parameters
    ----------
    owner: Vehicle
        The vehicle computing this force.
    obs_list: list of PointMass2d
        List of obstacles to check for avoidance.
    """

    # Obstacles closer than this distance will be avoided
    front_d = (1 + owner.vel.norm()/owner.maxspeed)*AVOID_MIN_LENGTH
    front_sq = front_d * front_d

    # Find the closest obstacle within the detection box
    xmin = 1 + front_d
    obs_closest = None
    for obstacle in obs_list:
        # Consider only obstacles that are nearby
        target = obstacle.pos
        diff = target - owner.pos
        if diff.sqnorm() < front_sq:
            # Convert to local coordinates of the owner
            local_x = diff / owner.front # This is an Orthogonal projection
            # Only consider objects in front
            if local_x > 0:
                # Find nearest x-intercept of extended bounding circle
                local_y = diff / owner.left
                expr = owner.radius + obstacle.radius
                xval = local_x - sqrt(expr*expr + local_y*local_y)
                # If this obstacle is closer, update minimum values
                if xval < xmin:
                    xmin, lx, ly = xval, local_x, local_y
                    obs_closest = obstacle

    # If there is a closest obstacle, avoid it
    if obs_closest:
        lr = obs_closest.radius
        lat_scale = (lr - ly)*(2.0 - lr / front_d)
        brake_scale = (lr - lx)*AVOID_BRAKE_WEIGHT
        result = owner.front.scale(brake_scale) + owner.left.scale(lat_scale)
        return result
    else:
        return Point2d(0,0)

def force_wallavoid(owner, whisk_len, wall_list):
    """Steering force for WALLAVOID behaviour, one front whisker"""

    closest_wall = None
    # Front whisker
    fr_min = whisk_len
    
    # Find the closest wall intersecting the foward whisker
    for wall in wall_list:
        # Is vehicle in front and whisker tip behind wall's infinite line?
        try:
            t = (wall.front * (wall.pos - owner.pos))/(wall.front * owner.front)
        except ZeroDivisionError:
            # Vehicle is facing parallel to wall in this case
            continue  
        if 0 < t < fr_min:
            # Is the point of intersection actually on the wall segment?
            poi = owner.pos + owner.front.scale(t)
            if (wall.pos - poi).sqnorm() < wall.rsq:
                # This is the closest intersecting wall so far
                closest_wall = wall
                closest_poi = poi
                fr_min = t
                
    if closest_wall is not None:
        target = closest_poi + closest_wall.front.scale((whisk_len - fr_min/2)*owner.vel.sqnorm())
        closest_wall.tagged = True
        return force_seek(owner, target)
    else:
        return Point2d(0,0)
        
def force_guard(owner, guard_this, guard_from, aggro):
    """Steering force for GUARD behavior.

    Parameters
    ----------
    owner: Vehicle
        The vehicle computing this force.
    guard_this: Vehicle
        The Vehicle that owner is guarding.
    guard_from: Vehicle
        The Vehicle that owner is guarding against.
    aggro: float
        Value from 0 to 1; controls aggressiveness (see notes below)

    Notes
    -----
    This is a more general version of INTERPOSE. The vehicle will attempt
    to position itself between guard_this and guard_from, at a relative
    distance controlled by aggro. Setting aggro near zero will position near
    guard_this; aggro near 1.0 will position near guard_from.

    The formula is the standard parameterization of a line segment, so we can
    actually set aggro outside of the unit interval.
    """

    # Find the desired position between the two objects as of now:
    target_pos = guard_this.pos
    from_pos = guard_from.pos
    want_pos = target_pos + (from_pos - target_pos).scale(aggro)

    # Predict future positions based on owner's distance/maxspeed to want_pos
    est_time = (want_pos - owner.pos).norm()/owner.maxspeed
    target_pos += guard_this.vel.scale(est_time)
    from_pos += guard_from.vel.scale(est_time)
    want_pos = target_pos + (from_pos - target_pos).scale(aggro)

    return force_arrive(owner, want_pos, 1.0)

def force_follow(owner, leader, offset):
    """Steering force for FOLLOW the leader at some offset.

    Parameters
    ----------
    owner: Vehicle
        The vehicle computing this force.
    leader: Vehicle
        The lead vehicle that the owner is following.
    offset: Point2d
        Offset from leader (in leader's local coordinates, front = +x)
    """

    target_pos = leader.pos + leader.front.scale(offset.x) + leader.left.scale(offset.y)
    diff = target_pos - owner.pos
    ptime = diff.norm() / (owner.maxspeed + leader.vel.norm())
    target_pos += leader.vel.scale(ptime)
    return force_arrive(owner, target_pos, 1.5)



class SteeringBehavior(object):
    """Helper class for managing a vehicle's autonomous steering.

    Each vehicle should maintain a reference to an instance of this class,
    and call compute_force() when an update is needed.

    Parameters
    ----------
    vehicle: PointMass2d
        The vehicle that will be steered by this instance
    """

    # TODO: Need some kind of interface to gameworld data here

    def __init__(self, vehicle):
        self.vehicle = vehicle
        self.status = {'SEEK': False,
                       'FLEE': False,
                       'ARRIVE': False,
                       'PURSUE': False,
                       'EVADE': False,
                       'WANDER': False,
                       'AVOID': False,
                       'WALLAVOID': False,
                       'GUARD': False,
                       'FOLLOW': False
                       }
        self.targets = dict()

    def set_target(self, **kwargs):
        """Initializes one or more steering behaviours.

        Parameters
        ----------
        SEEK: Point2d, optional
            If given, the vehicle will begin SEEKing towards this point.
        FLEE: Point2d, optional
            If given, the vehicle will begin FLEEing towards this point.
        ARRIVE: Point2d, optional
            If given, the vehicle will begin ARRIVEing towards this point.
        PURSUE: PointMass2d, optional
            If given, the vehicle will begin PURSUEing the prey.
        EVADE: PointMass2d, optional
            If given, the vehicle will begin EVADEing the predator
        WANDER: list of int or float, optional
            [Distance, Radius, Jitter]
        AVOID: list of PointMass2d, optional
            List of obstacles to be avoided.
        WALLAVOID: list of SimpleWall2d, optional
            List of walls to be avoided
        GUARD: [Vehicle, Vehicle, float], optional
            [GuardTarget, GuardFrom, AggressivePercent]
        FOLLOW: [Vehicle, Point2d], optional
            [Leader, OffsetFromLeader]

        """
        keylist = kwargs.keys()
        if 'SEEK' in keylist:
            target = kwargs['SEEK']
            # TODO: Error checking here.
            self.targets['SEEK'] = target
            self.status['SEEK'] = True
            print "SEEK active."

        if 'FLEE' in keylist:
            target = kwargs['FLEE']
            # TODO: Error checking here.
            self.targets['FLEE'] = target
            self.status['FLEE'] = True
            print "FLEE active."

        if 'ARRIVE' in keylist:
            target = kwargs['ARRIVE']
            # TODO: Error checking here.
            self.targets['ARRIVE'] = target
            self.status['ARRIVE'] = True
            print "ARRIVE active."

        if 'PURSUE' in keylist:
            prey = kwargs['PURSUE']
            # TODO: Error checking here.
            self.targets['PURSUE'] = prey
            self.status['PURSUE'] = True
            print "PURSUE active."

        if 'EVADE' in keylist:
            predator = kwargs['EVADE']
            # TODO: Error checking here.
            self.targets['EVADE'] = predator
            self.status['EVADE'] = True
            print "EVADE active."

        if 'WANDER' in keylist:
            wander_params = kwargs['WANDER']
            # TODO: Fix arguments, check errors
            wander_params.insert(0, self.vehicle.front)
            self.targets['WANDER'] = wander_params
            self.status['WANDER'] = True
            print "WANDER active."

        if 'AVOID' in keylist:
            obstacle_list = kwargs['AVOID']
            # TODO: Fix arguments, check errors
            # Currently we're passing a list of PointMass2d's
            self.obstacles = obstacle_list
            self.status['AVOID'] = True
            print "AVOID obstacles active."

        if 'WALLAVOID' in keylist:
            info = kwargs['WALLAVOID']
            # TODO: Fix arguments, check errors
            self.front_whisker= info[0]
            self.walls = info[1]
            self.status['WALLAVOID'] = True
            print "WALLAVOID active."
            
        if 'GUARD' in keylist:
            info = kwargs['GUARD']
            # TODO: Check for errors
            self.guard_this = info[0]
            self.guard_from = info[1]
            self.guard_aggr = info[2]
            self.status['GUARD'] = True
            print "GUARD active."

        if 'FOLLOW' in keylist:
            info = kwargs['FOLLOW']
            # TODO: Check for errors
            self.leader = info[0]
            self.leader_offset = info[1]
            self.status['FOLLOW'] = True
            print "FOLLOW leader active."

    def compute_force(self):
        """Find the required steering force based on current behaviors.

        Returns
        -------
        Point2d: Steering force.
        """
        # TODO: Add behaviours below
        # TODO: Iterate over self.status instead of using lots of if's
        force = Point2d(0,0)
        if self.status['SEEK'] is True:
            force += force_seek(self.vehicle, self.targets['SEEK'])
        if self.status['FLEE'] is True:
            #flee_from = self.avoid_this.pos
            force += force_flee(self.vehicle, self.targets['FLEE'])
        if self.status['ARRIVE'] is True:
            force += force_arrive(self.vehicle, self.targets['ARRIVE'])
        if self.status['PURSUE'] is True:
            force += force_pursue(self.vehicle, self.targets['PURSUE'])
        if self.status['EVADE'] is True:
            force += force_evade(self.vehicle, self.targets['EVADE'])
        if self.status['WANDER'] is True:
            force += force_wander(self)
        if self.status['AVOID'] is True:
            force += force_avoid(self.vehicle, self.obstacles)
        if self.status['WALLAVOID'] is True:
            force += force_wallavoid(self.vehicle, self.front_whisker, self.walls)
        if self.status['GUARD'] is True:
            force += force_guard(self.vehicle, self.guard_this, self.guard_from, self.guard_aggr)
        if self.status['FOLLOW'] is True:
            force += force_follow(self.vehicle, self.leader, self.leader_offset)
        return force





if __name__ == "__main__":
    print "Steering behavior functions. Import this elsewhere."
