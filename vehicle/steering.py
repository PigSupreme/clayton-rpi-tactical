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

# This contols the gradual deceleration for ARRIVE behavior.
# Larger values will cause more gradual deceleration
ARRIVE_DECEL_TWEAK = 10.0

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
        self.status = {'SEEK': False, 'FLEE': False, 'ARRIVE': False}
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
            print "FLEE active"

        if 'ARRIVE' in keylist:
            target = kwargs['ARRIVE']
            # TODO: Error checking here.
            self.targets['ARRIVE'] = target
            self.status['ARRIVE'] = True
            print "ARRIVE active"

    def compute_force(self):
        """Find the required steering force based on current behaviors.

        Returns
        -------
        Point2d: Steering force.
        """
        # TODO: Add behaviours below
        force = Point2d(0,0)
        if self.status['SEEK'] is True:
            force += force_seek(self.vehicle, self.targets['SEEK'])
        if self.status['FLEE'] is True:
            #flee_from = self.avoid_this.pos
            force += force_flee(self.vehicle, self.targets['FLEE'])
        if self.status['ARRIVE'] is True:
            force += force_arrive(self.vehicle, self.targets['ARRIVE'])
        return force





if __name__=="__main__":
    print "Steering behavior functions. Import this elsewhere."
