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
SQRT_HALF = sqrt(0.5)

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

# Avoid Walls: Percentage length of side whiskers relative to front whisker
WALLAVOID_WHISKER_SCALE = 0.8

# Take cover: For stalking, set this to cos^2(theta), where theta is the max
# angle from predator's front vector. The stalker will not hide unless within
# this angle of view.
TAKECOVER_STALK_T = 0.1 

# For simplicity, we multiply the vehicle's bounding radius by this constant
# to determine the local neighborhood radius for group behaviours.
FLOCKING_RADIUS_MULTIPLIER = 3.0

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

def force_wander(owner, steering):
    """Steering force for WANDER behavior.

    Parameters
    ----------
    owner: Vehicle
        The vehicle computing this force
    steering: SteeringBehavior
        An instance of SteeringBehavior (*not* a Vehicle, see note below)

    Note
    ----
    WANDER requires persistant data (specifically, the target of the wander
    circle), so we need access to the SteeringBehavior itself instead of the
    vehicle that owns it.
    """
    params = steering.wander_params
    jitter = params[2]

    # Add a random displacement to previous target and reproject
    target = steering.wander_target + Point2d(rand_uni(jitter), rand_uni(jitter))
    target.normalize()
    target = target.scale(params[1])
    steering.wander_target = target
    return force_seek(owner, owner.pos + target + owner.front.scale(params[0]))

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

def force_takecover(owner, predator, obs_list, max_range, stalk=False):
    """Steering force for TAKECOVER behind obstacle.
    
    Owner attempts to move to the nearest position that will put an obstacle
    between itself and the predator. If no such points are within max_range,
    EVADE the predator instead.
    
    MOAR COMMENTS HERE.
    """
    
    # If owner is stalking, don't hide unless in front of predator 
    if stalk:
        hide_dir = (owner.pos - predator.pos)
        if (hide_dir * predator.front)**2 < hide_dir.sqnorm()*TAKECOVER_STALK_T:
            return Point2d(0,0)
        
    
    best_dsq = max_range*max_range
    best_pos = None
    for obs in obs_list:
        # Find the hiding point for this obstacle
        hide_dir = (obs.pos - predator.pos).unit()
        hide_pos = obs.pos + hide_dir.scale(obs.radius + owner.radius)
        hide_dsq = (hide_pos - owner.pos).sqnorm()
        # Update distance and position if this obstacle is better
        if hide_dsq < best_dsq:
            best_pos = hide_pos
            best_dsq = hide_dsq
    
    if best_pos is None:
        return force_evade(owner, predator)
    else:
        return force_arrive(owner, best_pos, 1.0)

def force_wallavoid(owner, whisk_units, whisk_lens, wall_list):
    """Steering force for WALLAVOID behaviour with aribtrary whiskers.
    
    For each whisker, we find the wall with point of intersection closest
    to the base of the whisker. If such a wall is detected, it contributes a
    force in the direction of the wall normal proportional to the penetration
    depth of the whisker. Total force is the resultant vector sum.
    
    Parameters
    ----------
    owner: Vehicle
        The vehicle computing this force.
    whisk_units: list of Point2d or 2-tuple
        Whisker UNIT vectors in owner's local coordinates (forward is x+).
    whisk_lens: list of ositive int or float
        Lengths of whiskers, in same order as whisk_units above.
    wall_list: list of SimpleWall2d
        Walls to test for avoidance.        
    """

    n = len(whisk_units)
    whisk_front = n*[Point2d(0,0)]
    closest_wall = n*[None]
    
    # Covert unit vectors for each whisker to global coordinates
    for i in range(n):
        whisker = whisk_units[i]
        unit_whisker = owner.front.scale(whisker[0]) + owner.left.scale(whisker[1])
        whisk_front[i] = unit_whisker
        t_min = whisk_lens[:]
    
    # Find the closest wall intersecting each whisker
    for wall in wall_list:
        # TODO: Check against wall radius for better efficiency??        
        
        # Numerator of intersection test is the same for all whiskers
        t_numer = wall.front * (wall.pos - owner.pos)
        for i in range(n):
            # Is vehicle in front and whisker tip behind wall's infinite line?
            try:
                t = t_numer / (wall.front * whisk_front[i])
            except ZeroDivisionError:
                # Whisker is parallel to wall in this case, no intersection
                continue  
            if 0 < t < t_min[i]:
                # Is the point of intersection actually on the wall segment?
                poi = owner.pos + whisk_front[i].scale(t)
                if (wall.pos - poi).sqnorm() <= wall.rsq:
                    # This is the closest intersecting wall so far
                    closest_wall[i] = wall
                    t_min[i] = t
                    
    # For each whisker, add the force away from the closest wall (if any)
    result = Point2d(0,0)
    for i in range(n):
        if closest_wall[i] is not None:
            depth = whisk_lens[i] - t_min[i]
            result += closest_wall[i].front.scale(depth)

    # Scale by onwer radius; bigger objects should tend to stay away
    return result#.scale(owner.radius)
        
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

##############################################
### Group (flocking) behaviours start here ###
##############################################

def get_neighbor_vehicles(owner, vlist):
    """Returns a list of nearby vehicles for use with group behaviours.
    
    Parameters
    ----------
    owner: Vehicle
        The vehicle at the center of the neighborhood.
    vlist: List of Vehicle
        List of vehicles to be checked against. See Notes below.
        
    Notes
    -----
    This function checks other vehicles based only on their distance to owner.
    This allows for pre-processing (such as spaitial partitioning or flocking
    with certain vehicles only); the results of which are passed in as vlist.
    """
    n_radius = owner.radius * FLOCKING_RADIUS_MULTIPLIER
    neighbor_list = list()
    for other in vlist:
        if other is not owner:
            min_range = n_radius + other.radius
            offset = other.pos - owner.pos
            if offset.sqnorm() < min_range * min_range:
                neighbor_list.append(other)    
    return neighbor_list

def force_separate(owner, flock_list):
    """Steering force for SEPARATE group behaviour.
    
    Parameters
    ----------
    owner: Vehicle
        The vehicle computing this force.
    flock_list: List of Vehicle
        Neighboring vehicles to separate from.
        
    Notes
    -----
    For each neighbor, include a force away from that neighbor with magnitude
    inversely proprotional to distance from that neighbor.
    """
    # TODO: Update this with dynamic neighbors
    result = Point2d(0,0)
    neighbors = get_neighbor_vehicles(owner, flock_list)
    for other in neighbors:
        if other is not owner:
            offset = owner.pos - other.pos
            result += offset.scale(1/offset.sqnorm())
    return result

def force_align(owner, flock_list):
    """Steering force for ALIGN group behaviour."""
    # TODO: Update this with dynamic neighbors    
    result = Point2d(0,0)
    n = 0
    neighbors = get_neighbor_vehicles(owner, flock_list)
    for other in neighbors:
        if other is not owner:
            result += other.front
            n += 1
    if n > 0:
        result = result.scale(1.0/n)
        result -= owner.front
    return result
        
def force_cohesion(owner, flock_list):
    """Steering force for COHESION group behaviour."""
    # TODO: Update this with dynamic neighbors    
    center = Point2d(0,0)
    n = 0
    neighbors = get_neighbor_vehicles(owner, flock_list)
    for other in neighbors:
        if other is not owner:
            center += other.pos
            n += 1
    if n > 0:
        center = center.scale(1.0/n)
        return force_seek(owner, center)
    else:
        return Point2d(0,0)
            

#########################################################
### "Navigator-type class to control vehicle steering ###
#########################################################

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
                       'TAKECOVER': False,
                       'WANDER': False,
                       'AVOID': False,
                       'WALLAVOID': False,
                       'GUARD': False,
                       'FOLLOW': False,
                       'SEPARATE': False,
                       'ALIGN': False,
                       'COHESION': False
                       }
        self.targets = dict()

    def set_target(self, **kwargs):
        """Initializes one or more steering behaviours.

        Parameters
        ----------
        SEEK: (float, float), optional
            If given, the vehicle will begin SEEKing towards this point.
        FLEE: (float, float), optional
            If given, the vehicle will begin FLEEing towards this point.
        ARRIVE: (float, float), optional
            If given, the vehicle will begin ARRIVEing towards this point.
        PURSUE: PointMass2d, optional
            If given, the vehicle will begin PURSUEing the prey.
        EVADE: PointMass2d, optional
            If given, the vehicle will begin EVADEing the predator
        TAKECOVER: PointMass2d, optional
            If given, the vehicle will try to TAKECOVER from the predator.
        WANDER: tuple of int or float, optional
            (Distance, Radius, Jitter) for WANDER behaviour
        AVOID: tuple of PointMass2d, optional
            Tuple (iterable ok?) of obstacles to be avoided.
        WALLAVOID: tuple of SimpleWall2d, optional
            List of walls to be avoided
        GUARD: (Vehicle, Vehicle, float), optional
            (GuardTarget, GuardFrom, AggressivePercent)
        FOLLOW: (Vehicle, Point2d), optional
            (Leader, OffsetFromLeader)
        SEPARATE: List of Vehicle, optional
            Vehicle list to flock against
        ALIGN: List of Vehicle, optional
            Vehicle list to flock against
            
        Note
        ----
        Except for SEEK, FLEE, and ARRIVE, it might be possible to give
        the parameters for some behaviours as lists or sets. Test this.

        """
        keylist = kwargs.keys()
        if 'SEEK' in keylist:
            target = kwargs['SEEK']
            # TODO: Error checking here.
            self.targets[force_seek] = (Point2d(*target),)
            self.status['SEEK'] = True
            print "SEEK active."

        if 'FLEE' in keylist:
            target = kwargs['FLEE']
            # TODO: Error checking here.
            self.targets[force_flee] = (Point2d(*target),)
            self.status['FLEE'] = True
            print "FLEE active."

        if 'ARRIVE' in keylist:
            target = kwargs['ARRIVE']
            # TODO: Error checking here.
            self.targets[force_arrive] = (Point2d(*target),)
            self.status['ARRIVE'] = True
            print "ARRIVE active."

        if 'PURSUE' in keylist:
            prey = kwargs['PURSUE']
            # TODO: Error checking here.
            self.targets[force_pursue] = (prey,)
            self.status['PURSUE'] = True
            print "PURSUE active."

        if 'EVADE' in keylist:
            predator = kwargs['EVADE']
            # TODO: Error checking here.
            self.targets[force_evade] = (predator,)
            self.status['EVADE'] = True
            print "EVADE active."
            
        if 'TAKECOVER' in keylist:
            self.targets[force_takecover] = kwargs['TAKECOVER']
            self.status['TAKECOVER'] = True
            print "TAKECOVER active."
            
        if 'WANDER' in keylist:
            # TODO: Fix arguments, check errors
            self.wander_params = kwargs['WANDER']
            self.wander_target = self.vehicle.front
            # Next line may seem weird, but needed for unified interface.
            self.targets[force_wander] = (self,)
            self.status['WANDER'] = True
            print "WANDER active."

        if 'AVOID' in keylist:
            self.targets[force_avoid] = (kwargs['AVOID'],)
            # TODO: Fix arguments, check errors
            # Currently we're passing a list of PointMass2d's
            self.status['AVOID'] = True
            print "AVOID obstacles active."

        if 'WALLAVOID' in keylist:
            info = kwargs['WALLAVOID']
            # TODO: Fix arguments, check errors
            # Three whiskers: Front and left/right by 45 degrees
            whiskers = [Point2d(1,0), Point2d(SQRT_HALF, SQRT_HALF), Point2d(SQRT_HALF, -SQRT_HALF)]
            whisker_lengths = [info[0]] + 2*[info[0]*WALLAVOID_WHISKER_SCALE]
            self.targets[force_wallavoid] = [whiskers, whisker_lengths, info[1]]
            self.status['WALLAVOID'] = True
            print "WALLAVOID active"
            
        if 'GUARD' in keylist:
            self.targets[force_guard] = kwargs['GUARD']
            # TODO: Check for errors
            self.status['GUARD'] = True
            print "GUARD active."

        if 'FOLLOW' in keylist:
            self.targets[force_follow] = kwargs['FOLLOW']
            # TODO: Check for errors
            self.status['FOLLOW'] = True
            print "FOLLOW leader active."
            
        if 'SEPARATE' in keylist:
            n_list = kwargs['SEPARATE']
            self.vehicle.radius * FLOCKING_RADIUS_MULTIPLIER
            self.flocking = True
            # TODO: Make this neighbor-tagging dynamic
            self.targets[force_separate] = [n_list] 
            self.status['SEPARATE'] = True
            print 'SEPARATE (flocking) active.'

        if 'ALIGN' in keylist:
            n_list = kwargs['ALIGN']
            self.vehicle.radius * FLOCKING_RADIUS_MULTIPLIER
            self.flocking = True
            # TODO: Make this neighbor-tagging dynamic
            self.targets[force_align] = [n_list] 
            self.status['ALIGN'] = True
            print 'ALIGN (flocking) active.'
            
        if 'COHESION' in keylist:
            n_list = kwargs['COHESION']
            self.vehicle.radius * FLOCKING_RADIUS_MULTIPLIER
            self.flocking = True
            # TODO: Make this neighbor-tagging dynamic
            self.targets[force_cohesion] = [n_list] 
            self.status['COHESION'] = True
            print 'COHESION (flocking) active.'

    def compute_force(self):
        """Find the required steering force based on current behaviors.

        Returns
        -------
        Point2d: Steering force.
        """
        force = Point2d(0,0)     
        owner = self.vehicle
        # This assumes self.targets is a dictionary with keys equal to 
        # appropriate force_foo functons, and values equal to the parameters
        # to be passed. All force_ functions take a vehicle as their first
        # argument; we look this up here and do not store in self.targets.
        for f, t in self.targets.iteritems():
            force += f(owner, *t)
        return force

    def compute_force_budgeted(self):
        # TODO: Set this up!
        pass




if __name__ == "__main__":
    print "Steering behavior functions. Import this elsewhere."
