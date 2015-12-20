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

# This controls the size of an object detection box for AVOID obstacles
# Length in front of vehicle is 100%-200% of this
AVOID_MIN_LENGTH = 25.0
AVOID_BRAKE_WEIGHT = 2.0


# Random number generator
from random import Random
rand_gen = Random()
rand_gen.seed()
rand_uni = lambda x: rand_gen.uniform(-x,x)



def force_seek(owner, target):
    """Steering force for Seek behaviour.

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
    """Steering force for Flee behaviour,

    Parameters
    ----------
    owner: Vehicle
        The vehicle computing this force.
    position: Point2d
        The target point that owner is fleeing from.
    panic_squared: float
        If specified, only compute a flee_force if squared distance
        to the target is less than this value. Otherwise
    """
    targetvel = (owner.pos - target)
    if 1 < targetvel.sqnorm() < panic_squared:
        targetvel = targetvel.unit().scale(owner.maxspeed)
        return targetvel - owner.vel
    else:
        return Point2d(0,0)

def force_arrive(owner, target, hesitance=2.0):
    """Steering force for Arrive behaviour.

    This works like Seek, except the vehicle gradually deccelerates as it
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
    """Steering force for PURSUE behaviour."""

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
    """Steering force for EVADE behaviour."""

    predator_offset = predator.pos - owner.pos
    # Predict the future position of predator, assuming it has a constant
    # velocity. Prediction time is the distance to predator divided
    # by the sum of our max speed and predator's current speed.
    ptime = predator_offset.norm()/(owner.maxspeed + predator.vel.norm())
    return force_flee(owner, predator.vel.scale(ptime) + predator.pos, 10000)

def force_wander(steer):
    """Steering force for WANDER behavior.

    Parameters
    ----------
    steer: SteeringBehavior
        Comment here.

    Note
    ----
    Since the more complex behaviors might need persistant data (in this case,
    values related to the wander circle), it might be better to rework the
    simple behaviors to use an instance of SteeringBehavior as their first
    parameter, rather than an instance of vehicle. Ponder this.
    """
    owner = steer.vehicle
    target, dist, rad, jitter = steer.targets['WANDER']

    # Add a random displacement to previous target and reproject
    target += Point2d(rand_uni(jitter),rand_uni(jitter))
    target.normalize()
    target = target.scale(rad)
    steer.targets['WANDER'][0] = target
    return force_seek(owner, owner.pos + target + owner.front.scale(dist))

def force_avoid(steer):
    """Steering force for AVOID obstacle behavior.

    Parameters
    ----------
    steer: SteeringBehavior
        Comment here.
    """

    owner = steer.vehicle
    left = owner.front.left_normal()
    # Obstacles closer than this distance will be avoided
    front_d = (1 + owner.vel.sqnorm()/owner.maxspeed)*AVOID_MIN_LENGTH
    front_sq = front_d * front_d

    # Find the closest obstacle within the detection box
    xmin = 1 + front_d
    obs_closest = None
    for obstacle in steer.obstacles:
        # Consider only obstacles that are nearby
        target = obstacle.pos
        diff = target - owner.pos
        if diff.sqnorm() < front_sq:
            # Convert to local coordinates
            local_x = diff / owner.front # This is an Orthogonal projection
            # Only consider objects in front
            if local_x > 0:
                obstacle.tagged = True
                # Find nearest x-intercept of extended bounding circle
                local_y = diff / left
                expr = owner.radius + obstacle.radius
                xval = local_x - sqrt(expr*expr + local_y*local_y)
                if xval < xmin:
                    xmin, lx, ly = xval, local_x, local_y
                    obs_closest = obstacle

    if obs_closest:
        lr = obs_closest.radius
        lat_scale = (lr - ly)*(2.0 - lr / front_d)
        brake_scale = (lr - lx)*AVOID_BRAKE_WEIGHT
        result = owner.front.scale(brake_scale) + left.scale(lat_scale)
        return result
    else:
        return Point2d(0,0)


class SteeringBehavior(object):
    """Help class for managing a vehicle's autonomous steering.

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
                       'AVOID': False
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
        WANDER: list
            [Distance, Radius, Jitter]
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
            wander_params.insert(0,self.vehicle.front)
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
            force += force_avoid(self)
        return force





if __name__=="__main__":
    print "Steering behavior functions. Import this elsewhere."
