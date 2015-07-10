# -*- coding: utf-8 -*-
"""Module containing BOID steering behavior functions.

Since we typically won't need every single behaviour for a given instance,
import the needed ones from this module. The function that returns the force
for a given behaviour is named force_name-of-behviour.
"""

from sys import path
path.insert(0,'../vpoints')
from point2d import Point2d
INF = float('inf')

def force_seek(owner, target):
    """Steering force for Seek behaviour.
    
    Parameters
    ----------
    owner: Vehicle
        The vehicle computing this force.
    position: Point2d
        The target point that owner is seeking to.

    Note
    ----
    This is the version in steering.py
    """
    targetvel = (target - owner.pos).unit()
    targetvel = targetvel.scale(owner.maxspeed)
    return (targetvel - owner.vel)

def force_flee(owner, target, panic_squared = INF):
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

    Note
    ----
    This is the version in steering.py
    """
    targetvel = (owner.pos - target)
    if 1 < targetvel.sqnorm() < panic_squared:
        targetvel = targetvel.unit().scale(owner.maxspeed)
        return (targetvel - owner.vel)
    else:
        return Point2d(0,0)
        
def force_arrive(owner,target,hesitance=2.0):
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
        gradual (and slow) decceleration. Suggested values are 1.0 - 5.0.
        
    Note
    ----
    This is the version in steering.py
    """
    target_offset = (target - owner.pos)
    dist = target_offset.norm()
    if dist > 0:
        # The constant on the next line may need tweaking
        speed = dist / (0.2 * hesitance)
        if speed > owner.maxspeed:
            speed = owner.maxspeed    
        targetvel = target_offset.scale(speed/dist)
        return targetvel
    else:
        return Point2d(0,0)
