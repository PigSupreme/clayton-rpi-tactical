# steering.py
"""Module containing PyBOID steering behavior functions.

Each type of behaviour needs a force_foo() function to compute the actual
steering force. The first argument ("owner") is the vehicle that is being
steered. Any number of additional arguments are permitted. This allows the
SteeringBehaviour.compute_force functions to automatically call each active
behaviour's force_foo() function with appropriate arguments.

Each behaviour also needs a activate_foo() function. The first argument
("steering") is an instance of SteeringBehaviour owned by the given vehicle;
additional arguments are intended to be stored within the SteeringBehaviour
instance and then passed to the corresponding force_foo() each update. See
the SEEK code for a simple example.

Importing this module will automatically generate a BEHAVIOUR_LIST containing
all behaviours that follow the conventions above. This makes it very easy to
add additional behaviours with minimal changes to the existing code (besides
writing the force/activate functions, SteeringBehaviour.PRIORITY_LIST would
need to be modified if using budgeted force).

TODO: SteeringBehavious.flocking is not automatically updated by pause, stop,
and resume methods. FIX THIS!

TODO: Future versions might provide a mechanism for importing only a subset
of the available behaviours, but this isn't really needed at this time.
"""

# for python3 compat
from __future__ import unicode_literals
from __future__ import absolute_import
from __future__ import print_function
from __future__ import division

from sys import path
path.extend(['../vpoints'])
from point2d import Point2d

# Constants for steering behaviours
from steering_constants import *

# Math Constants (for readability)
INF = float('inf')
from math import sqrt
SQRT_HALF = sqrt(0.5)

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
    owner: SimpleVehicle2d
        The vehicle computing this force.
    position: Point2d
        The target point that owner is seeking to.
    """
    targetvel = (target - owner.pos).unit()
    targetvel = targetvel.scale(owner.maxspeed)
    return targetvel - owner.vel

def activate_seek(steering, target):
    """Activate SEEK behaviour."""
    # TODO: Error checking here.
    steering.targets[force_seek] = (Point2d(*target),)
    return True

def force_flee(owner, target, panic_squared=FLEE_PANIC_SQ):
    """Steering force for FLEE behaviour.

    Another simple behaviour that directs the owner away from a given point.

    Parameters
    ----------
    owner: SimpleVehicle2d
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

def activate_flee(steering, target):
    """Activate FLEE behaviour."""
    # TODO: Error checking here.
    # TODO: Provide a way to set individual panic_squared values??
    steering.targets[force_flee] = (Point2d(*target),)
    return True

def force_arrive(owner, target, hesitance=2.0):
    """Steering force for ARRIVE behaviour.

    This works like SEEK, except the vehicle gradually deccelerates as it
    nears the target position. The optional third parameter controls the
    amount of decceleration.

    Parameters
    ----------
    owner: SimpleVehicle2d
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

def activate_arrive(steering, target):
    if len(target) == 2:
        steering.targets[force_arrive] = (Point2d(*target),)
    else:
        steering.targets[force_arrive] = (Point2d(target[0], target[1]), target[2])
    return True

def force_pursue(owner, prey):
    """Steering force for PURSUE behaviour.

    Similar to SEEK, but lead the prey by estimating its future location,
    based on current velocities.

    Parameters
    ----------
    owner: SimpleVehicle2d
        The vehicle computing this force.
    prey: BasePointMass2d
        The vehicle that owner will pursue.
    """
    prey_offset = prey.pos - owner.pos
    # If prey is in front and moving our way, SEEK to prey's position
    # Compute this using dot products; constant below is cos(10 degrees)
    # TODO: Double-check the math on this. Do we need to account for the
    #   vectors being non-unit, or check that we're actually facing prey?
    if prey_offset * prey.vel < -0.966:
        return force_seek(owner, prey.pos)

    # Otherwise, predict the future position of prey, assuming it has a
    # constant velocity. Prediction time is the distance to prey, divided
    # by the sum of our max speed and prey's current speed.
    ptime = prey_offset.norm()/(owner.maxspeed + prey.vel.norm())
    return force_seek(owner, prey.vel.scale(ptime) + prey.pos)

def activate_pursue(steering, prey):
    # TODO: Error checking here.
    steering.targets[force_pursue] = (prey,)
    return True
    
def force_evade(owner, predator):
    """Steering force for EVADE behaviour.

    Similar to FLEE, but try to get away from the predicted future position
    of the predator. Predators far away are ignored, EVADE_PANIC_SQ is used
    to control the panic distance passed to FLEE.

    Parameters
    ----------
    owner: SimpleVehicle2d
        The vehicle computing this force.
    predator: BasePointMass2d
        The vehicle that owner will pursue.
    """
    predator_offset = predator.pos - owner.pos
    # Predict the future position of predator, assuming it has a constant
    # velocity. Prediction time is the distance to predator divided
    # by the sum of our max speed and predator's current speed.
    ptime = predator_offset.norm()/(owner.maxspeed + predator.vel.norm())
    return force_flee(owner, predator.vel.scale(ptime) + predator.pos, EVADE_PANIC_SQ)

def activate_evade(steering, predator):
    # TODO: Error checking here.
    steering.targets[force_evade] = (predator,)
    return True

def force_wander(owner, steering):
    """Steering force for WANDER behavior.

    Parameters
    ----------
    owner: SimpleVehicle2d
        The vehicle computing this force
    steering: SteeringBehavior
        An instance of SteeringBehavior (*not* a vehicle, see note below)

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

def activate_wander(steering, target):
    # TODO: Fix arguments, check errors
    steering.wander_params = target
    steering.wander_target = steering.vehicle.front
    # Next line may seem weird, but needed for unified interface.
    steering.targets[force_wander] = (steering,)
    return True

def force_avoid(owner, obs_list):
    """Steering force for AVOID stationary obstacles behaviour.

    This projects a box in front of the owner and tries to find an obstacle
    for which collision is imminent (not always the closest obstacle). The
    owner will attempt to steer around that obstacle.

    Parameters
    ----------
    owner: SimpleVehicle2d
        The vehicle computing this force.
    obs_list: list of BasePointMass2d
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

def activate_avoid(steering, target):
    steering.targets[force_avoid] = (target,)
    # TODO: Fix arguments, check errors
    # Currently we're passing a list of SimpleObstacle2d
    return True

def force_takecover(owner, target, obs_list, max_range, stalk=False):
    """Steering force for TAKECOVER behind obstacle.

    Owner attempts to move to the nearest position that will put an obstacle
    between itself and the target. If no such points are within max_range,
    EVADE the predator instead.
    
    By setting stalk to True, we'll only hide when in front of the target.
    Stalking allows this vehicle to (somewhat clumsily) sneak up from behind.

    Parameters
    ----------
    owner: SimpleVehicle2d
        The vehicle computing this force.
    target: BasePointMass2d
        The vehicle we try to hide from.
    obs_list: list of BasePointMass2d
        List of obstacles to check for avoidance.
    max_range: float
        Obstacles further than this value are ignored.
    stalk: boolean
        If True, only hide when we are in front of the target.
    """

    # If we're stalking, only hide when we're in front of our target.
    if stalk:
        hide_dir = (owner.pos - target.pos)
        if (hide_dir * target.front)**2 < hide_dir.sqnorm()*TAKECOVER_STALK_T:
            return Point2d(0,0)

    best_dsq = max_range*max_range
    best_pos = None
    for obs in obs_list:
        # Find the hiding point for this obstacle
        hide_dir = (obs.pos - target.pos).unit()
        hide_pos = obs.pos + hide_dir.scale(obs.radius + owner.radius)
        hide_dsq = (hide_pos - owner.pos).sqnorm()
        # Update distance and position if this obstacle is better
        if hide_dsq < best_dsq:
            best_pos = hide_pos
            best_dsq = hide_dsq

    if best_pos is None:
        return force_evade(owner, target)
    else:
        return force_arrive(owner, best_pos, 1.0)

def activate_takecover(steering, target):
    # TODO: Error checking
    steering.targets[force_takecover] = target
    return True
            
def force_wallavoid(owner, whisk_units, whisk_lens, wall_list):
    """Steering force for WALLAVOID behaviour with aribtrary whiskers.

    For each whisker, we find the wall with point of intersection closest
    to the base of the whisker. If such a wall is detected, it contributes a
    force in the direction of the wall normal proportional to the penetration
    depth of the whisker. Total force is the resultant vector sum.

    Parameters
    ----------
    owner: SimpleVehicle2d
        The vehicle computing this force.
    whisk_units: list of Point2d or 2-tuple
        Whisker UNIT vectors in owner's local coordinates (forward is x+).
    whisk_lens: list of positive int or float
        Lengths of whiskers, in same order as whisk_units above.
    wall_list: list of BaseWall2d
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

    # Scale by owner radius; bigger objects should tend to stay away
    return result.scale(owner.radius)

def activate_wallavoid(steering, info):
    # TODO: Fix arguments, check errors
    # Three whiskers: Front and left/right by 45 degrees
    whiskers = [Point2d(1,0), Point2d(SQRT_HALF, SQRT_HALF), Point2d(SQRT_HALF, -SQRT_HALF)]
    whisker_lengths = [info[0]] + 2*[info[0]*WALLAVOID_WHISKER_SCALE]
    steering.targets[force_wallavoid] = [whiskers, whisker_lengths, info[1]]
    return True

def force_guard(owner, guard_this, guard_from, aggro):
    """Steering force for GUARD behavior.

    Parameters
    ----------
    owner: SimpleVehicle2d
        The vehicle computing this force.
    guard_this: BasePointMass2d
        The target that owner is guarding.
    guard_from: BasePointMass2d
        The target that owner is guarding against.
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

def activate_guard(steering, target):
    steering.targets[force_guard] = target
    # TODO: Check for errors
    return True

def force_follow(owner, leader, offset):
    """Steering force for FOLLOW the leader at some offset.

    Parameters
    ----------
    owner: SimpleVehicle2d
        The vehicle computing this force.
    leader: BasePointMass2d
        The lead vehicle that the owner is following.
    offset: Point2d
        Offset from leader (in leader's local coordinates, front = +x)
    """

    target_pos = leader.pos + leader.front.scale(offset.x) + leader.left.scale(offset.y)
    diff = target_pos - owner.pos
    ptime = diff.norm() / (owner.maxspeed + leader.vel.norm())
    target_pos += leader.vel.scale(ptime)
    return force_arrive(owner, target_pos, FOLLOW_ARRIVE_HESITANCE)

def activate_follow(steering, target):
    steering.targets[force_follow] = target
    # TODO: Check for errors
    return True

def force_brake(owner, decay=0.5):
    """Steering force oppoisite of current forward velocity.
    
    Parameters
    ----------
    owner: SimpleVehicle2d
        The vehicle computing this force.
    decay: float
        Discrete exponential decay constant for speed; 0 < decay < 1.
    """
    speed = owner.vel.norm()
    return owner.vel.scale(-decay * speed)

def activate_brake(steering, target):
    # TODO: Error checking here.
    if 0 < target < 1:
        steering.targets[force_brake] = (target,)
    else:
        steering.targets[force_brake] = (0.5,)
    return True

##############################################
### Path-following behaviours start here   ###
##############################################

class SteeringPath(object):
    """Helper class for managing path-related behaviour.
    
    Parameters
    ----------
    waypoints: list of Point2d
        Non-empty list of waypoints on this path.
    is_cyclic: boolean
        If set to True, path will automatically cycle. See notes below.
        
    Notes
    -----
    When using this for vehicle steering, the first waypoint is intended as the
    starting point of some owner vehicle. This point is *not* automatically put
    back on the path even if is_cyclic is set to True, so add it manually to the
    end of waypoints list if the vehicle should return to its starting point.
    """
    
    def __init__(self, waypoints, is_cyclic=False):
        self.waypoints = waypoints
        self.is_cyclic = is_cyclic
        
        # Compute initial segment, see Notes
        self.oldway = self.waypoints.pop(0)
        self.newway = self.waypoints.pop(0)
        # Length of this edge and unit vector (oldway to newway)
        offset = self.newway - self.oldway
        self.edgelength = offset.norm()
        if self.edgelength > 0:
            self.edgevector = offset.scale(1/self.edgelength)
        else:
            self.edgevector = Point2d(0,0)
            print("[%s] Warning: duplciate waypoint at %s" % (self,self.newway))
        if not is_cyclic:
            # Add a dummy waypoint to signal end of path
            self.waypoints.append(None)
        
    def advance(self):
        """Update our waypoints to the next segment on the path."""
        self.oldway = self.newway
        if self.is_cyclic:
            self.waypoints.append(self.newway)
        try:
            self.newway = self.waypoints.pop(0)
            # TODO: Check for empty path, rewrite try/execpt block
            # Compute new length and unit vector
            offset = self.newway - self.oldway
            self.edgelength = offset.norm()
            if self.edgelength > 0:
                self.edgevector = offset.scale(1/self.edgelength)
            else:
                self.edgevector = Point2d(0,0)
                print("[%s] Warning: duplciate waypoint at %s" % (self,self.newway))
        except TypeError:
            # self.oldway was the last waypoint on the path
            self.newway = None
            self.edgelength = 0
            self.edgevector = Point2d(0,0)

            
def force_pathfollow(owner, path):
    """Steering force for PATHFOLLOW behaviour.
    
    Parameters
    ----------
    owner: SimpleVehicle2d
        The vehicle computing this force.
    path: SteeringPath
        Path to be followed by the owner
        
    Notes
    -----
    This is the simplest version, SEEK to next waypoint.
    """
    # TODO: Clean up this nonsense!
    # If no waypoint left, exit immediately
    if path.newway is None:
        return Point2d(0,0)
        
    # Otherwise, check for arrival
    if (owner.pos - path.newway).sqnorm() <= PATHFOLLOW_TOLERANCE_SQ:
        path.advance()
        
    if path.newway is None:
        return Point2d(0,0)
    
    # TODO: This is for testing only?
    owner.waypoint = path.newway
    
    return force_seek(owner, path.newway)
        
def activate_pathfollow(steering, path):
    """Activate PATHFOLLOW behaviour."""
    # TODO: Error checking here.
    steering.targets[force_pathfollow] = (path,)
    return True

def force_pathresume(owner, path, invk):
    """Steering force for PATHRESUME behaviour.

    Parameters
    ----------
    owner: SimpleVehicle2d
        The vehicle computing this force.
    path: SteeringPath
        Path to be followed by the owner
    invk: positive float
        Reciprocal of exponential decay constant. See Notes.
        
    Notes
    -----
    If the vehicle is off course, this will give a balance between returning
    directly to the current path edge and SEEKing to the next waypoint.
    Smaller value of invk (larger decay rate) give more immediate return to
    the path.
    TODO: Further comments are probably needed.
    """
    # TODO: Clean up this nonsense!
    # If no waypoint left, exit immediately
    if path.newway is None:
        return Point2d(0,0)
        
    # Otherwise, check for arrival
    if (owner.pos - path.newway).sqnorm() <= PATHFOLLOW_TOLERANCE_SQ:
        path.advance()
        
    if path.newway is None:
        return Point2d(0,0)
    
    # TODO: This is for testing only?
    owner.waypoint = path.newway
    
    # This is the remaining direct distance to the next waypoint,
    # using orthogonal projection operator. If the old/new waypoints
    # are identical, the Point2d code throws the error, and we can
    # simply SEEK to the next waypoint
    try:
        rl = (path.newway - owner.pos)/path.edgevector
    except ZeroDivisionError:
        rl = 0
        
    # If resume target is beyond the next waypoint, SEEK to next waypoint.
    # Otherwise, SEEK to the resume target
    if invk >= rl:
        target = path.newway
    else:
        target = path.newway + path.edgevector.scale(invk - rl)
    
    return force_seek(owner, target)

def activate_pathresume(steering, path, dekay=PATHRESUME_DECAY):
    """Activate PATHRESUME behaviour."""
    # TODO: Error checking here.
    steering.targets[force_pathresume] = (path, 1.0/dekay)
    return True

##############################################
### Group (flocking) behaviours start here ###
##############################################

def force_separate(owner):
    """Steering force for SEPARATE group behaviour.

    Parameters
    ----------
    owner: SimpleVehicle2d
        The vehicle computing this force.

    Notes
    -----
    All flocking forces use owner.neighbor_list to find a flock; set this list
    before calling this function.

    For each neighbor, include a force away from that neighbor with magnitude
    proportional to the neighbor radius and inversely proprotional to distance.
    This gave nicer results and allows us to cleverly avoid computing a sqrt.
    """
    result = Point2d(0,0)
    for other in owner.neighbor_list:
        if other is not owner:
            offset = owner.pos - other.pos
            result += offset.scale(FLOCKING_SEPARATE_SCALE*other.radius/offset.sqnorm())
    return result

def activate_separate(steering, n_list):
    steering.flocking = True
    # TODO: Check for errors
    steering.targets[force_separate] = ()
    steering.flockmates = n_list[:]
    return True

def force_align(owner):
    """Steering force for ALIGN group behaviour.

    Parameters
    ----------
    owner: SimpleVehicle2d
        The vehicle computing this force.

    Notes
    -----
    All flocking forces use owner.neighbor_list to find a flock; set this list
    before calling this function.

    Unlike(?) traditional boids, we ALIGN with the average of neighbors'
    velocity vectors. Align with heading (normalize velocity) looked weird.
    """
    result = Point2d(0,0)
    n = 0
    for other in owner.neighbor_list:
        if other is not owner:
            result += other.vel
            n += 1
    if n > 0:
        result = result.scale(1.0/n)
        result -= owner.front
    return result

def activate_align(steering, n_list):
    steering.flocking = True
    # TODO: Check for errors
    steering.targets[force_align] = ()
    steering.flockmates = n_list[:]
    return True
    
def force_cohesion(owner):
    """Steering force for COHESION group behaviour.

    Parameters
    ----------
    owner: SimpleVehicle2d
        The vehicle computing this force.

    Notes
    -----
    All flocking forces use owner.neighbor_list to find a flock; set this list
    before calling this function.
    """
    
    center = Point2d(0,0)
    n = 0
    for other in owner.neighbor_list:
        if other is not owner:
            center += other.pos
            n += 1
    if n > 0:
        center = center.scale(1.0/n)
        return force_arrive(owner, center, FLOCKING_COHESHION_HESITANCE)
    else:
        return Point2d(0,0)

def activate_cohesion(steering, n_list):
    steering.flocking = True
    # TODO: Check for errors
    steering.targets[force_cohesion] = ()
    steering.flockmates = n_list[:]
    return True

########################################################
## Auto-generate a list of behaviours above, along with
## dictionaries to reference their force/activate fnc's.
## This allows us to easily add behaviours later.
########################################################
BEHAVIOUR_LIST = [x[6:].upper() for x in locals().keys()[:] if (x[:6]=='force_')]
FORCE_FNC = dict()
ACTIVATE_FNC = dict()
for behaviour in BEHAVIOUR_LIST[:]:
    try:
        force_fnc = locals()['force_' + behaviour.lower()] 
        activate_fnc = locals()['activate_' + behaviour.lower()]
        FORCE_FNC[behaviour] = force_fnc
        ACTIVATE_FNC[behaviour] = activate_fnc
    except KeyError:
        print("[steering.py] Warning: could not define behaviour %s." % behaviour)
        BEHAVIOUR_LIST.remove(behaviour)
        
########################################################
### Navigator-type class to control vehicle steering ###
########################################################

class SteeringBehavior(object):
    """Helper class for managing a vehicle's autonomous steering.

    Each vehicle should maintain a reference to an instance of this class,
    and call the compute_force() method when an update is needed.

    Parameters
    ----------
    vehicle: SimpleVehicle2d
        The vehicle that will be steered by this instance
    use_budget: boolean
        Default (True) uses vehicle's maxforce as a force budget per update.
        If set to False, all active behaviors are consdidered each update.
    """

    PRIORITY_DEFAULTS = ['BRAKE',
                         'WALLAVOID',
                         'AVOID',
                         'SEPARATE',
                         'FLEE',
                         'EVADE',
                         'SEEK',
                         'ARRIVE',
                         'TAKECOVER',
                         'PURSUE',
                         'GUARD',
                         'FOLLOW',
                         'PATHRESUME',
                         'PATHFOLLOW',
                         'COHESION',
                         'ALIGN',
                         'WANDER'
                         ]

    # TODO: Need some kind of interface to gameworld data here??
    def __init__(self, vehicle, use_budget=True):
        self.vehicle = vehicle
        self.status = {beh: False for beh in BEHAVIOUR_LIST}
        self.targets = dict()
        self.inactive_targets = dict()
        self.flocking = False   
        
        # Set the appropriate compute_force_ function here.
        if use_budget is True:
            self.compute_force = self.compute_force_budgeted
            # Kludge function to sort behaviours by order in PRIORITY_DEFAULTS
            # This removes each 'force_' part and converts to UPPERCASE
            self.priority_key = lambda fnc: SteeringBehavior.PRIORITY_DEFAULTS.index(fnc[0].func_name[6:].upper())
            self.set_priorities()
        else:
            self.compute_force = self.compute_force_simple

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
        PURSUE: BasePointMass2d, optional
            If given, the vehicle will begin PURSUEing the prey.
        EVADE: BasePointMass2d, optional
            If given, the vehicle will begin EVADEing the predator
        TAKECOVER: BasePointMass2d, optional
            If given, the vehicle will try to TAKECOVER from the predator.
        WANDER: tuple of int or float, optional
            (Distance, Radius, Jitter) for WANDER behaviour
        AVOID: tuple of BasePointMass2d, optional
            Tuple (iterable ok?) of obstacles to be avoided.
        WALLAVOID: tuple of BaseWall2d, optional
            List of walls to be avoided
        GUARD: (BasePointMass2d, BasePointMass2d, float), optional
            (GuardTarget, GuardFrom, AggressivePercent)
        FOLLOW: (BasePointMass2d, Point2d), optional
            (Leader, OffsetFromLeader)
        SEPARATE: List of BasePointMass2d, optional
            List of targets to flock with
        ALIGN: List of BasePointMass2d, optional
            List of targets to flock with
        COHESION: List of BasePointMass2d, optional
            List of targets to flock with
        BRAKE: float, optional
            Speed decay factor (0 < decay < 1)

        Notes
        -----
        Flocking behaviours (SEPARATE, ALIGN, COHESION) automatically set
        self.flocking to True; this is used by force_foo functions so that
        neighbors need only be tagged once per cycle (for efficiency).
        
        TODO: Parameters for path-related behaviour
        """
        for (behaviour, target) in kwargs.items():
            # Find and call correponding activate function
            try:
                # The activate_foo function must be defined above
                activate_fnc = ACTIVATE_FNC[behaviour]
                result = activate_fnc(self, target)
                if result is True:
                    self.status[behaviour] = True
                    print('%s successfully initiated.' % behaviour)
            except KeyError:
                print("Warning: %s behaviour improperly defined; cannot activate." % behaviour)

        self.set_priorities()

    def pause(self, steering_type):
        """Temporarilily turns off a steering behaviour, keeping targets."""
        try:
            fnc = FORCE_FNC[steering_type]
            self.inactive_targets[steering_type] = self.targets[fnc]
            del self.targets[fnc]
            self.status[steering_type] = False
            self.set_priorities()
            print('%s paused.' % steering_type)
        except KeyError:
            print('Warning: Behaviour %s has not been initialized. Ignoring pause.' % steering_type)

    def resume(self, steering_type):
        """Turns on a previously paused behaviour, using old targets."""
        # TODO: Check that this behaviour was previous initialized
        try:
            fnc = FORCE_FNC[steering_type]
            target = self.inactive_targets[steering_type]
            self.targets[fnc] = target
            del self.inactive_targets[fnc]
            self.status[steering_type] = True
            self.set_priorities()
        except KeyError:
            print('Warning: Behaviour %s was not paused. Ignoring resume.' % steering_type)

    def stop(self, steering_type):
        """Permanently turns off a steering behaviour until re-initialized."""
        try:
            fnc = FORCE_FNC[steering_type]
            del self.targets[fnc]
            self.status[steering_type] = False
            self.set_priorities()
            print('%s stopped.' % steering_type)
        except KeyError:
            print('Warning: Behaviour %s has not been initialized. Ignoring stop.' % steering_type)
 

    def flag_neighbor_vehicles(self, vlist=()):
        """Populates a list of nearby vehicles, for use with flocking

        Parameters
        ----------
        owner: SimpleVehicle2d
            Neighbors of this vehicle will be updated. See Notes below.
        vlist: List of BasePointMass2d
            List of vehicles to be checked against. See Notes below.

        Notes
        -----
        This function checks other vehicles based on their distance to owner and
        includes only vehicles in front of the owner. Maximum distnance is the
        owner's radius times FLOCKING_RADIUS_MULTIPLIER. We may consider more
        sophisticated sensing of neighbors in the future.

        Results of flagging are stored as owner.neighbor_list to be read later by
        force_foo functions that require this info. Be sure to run this function
        before any such force_foo functions (mostly for flocking).

        This is designed to work with pre-processing (such as spatial partitioning
        or flocking with certain vehicles only); the results of which are passed
        in as vlist. If this isn't needed,
        
        TODO: Current implementation does not use vlist(), and the above comment
        is clearly incomplete. Figure out what's going on here and fix it.
        """
        owner = self.vehicle
        n_radius = owner.radius * FLOCKING_RADIUS_MULTIPLIER
        neighbor_list = list()
        # TODO: Pre-process self.flockmates and loop over that result.
        for other in self.flockmates:
            if other is not owner:
                min_range = n_radius + other.radius
                offset = other.pos - owner.pos
                if offset.sqnorm() < min_range * min_range:
                    # Only consider neighbors to the front
                    if offset*owner.front >=0:
                        neighbor_list.append(other)
        owner.neighbor_list = neighbor_list

    def compute_force_simple(self):
        """Find the required steering force based on current behaviors.

        Returns
        -------
        Point2d: Steering force.
        """
        force = Point2d(0,0)
        owner = self.vehicle
        # TODO: If any flocking is active, determine neighbors first
        if self.flocking is True:
            self.flag_neighbor_vehicles(self.flockmates)

        # This assumes self.targets is a dictionary with keys equal to
        # appropriate force_foo functons, and values equal to the parameters
        # to be passed. All force_ functions take a vehicle as their first
        # argument; we look this up here and do not store in self.targets.
        for f, t in self.targets.iteritems():
            force += f(owner, *t)
            # TODO: Check for active behaviours; see budgeted version below
        force.truncate(owner.maxforce)
        return force

    def set_priorities(self):
        """Create a prioritized list of steering behaviours for later use."""
        self.priorities = sorted(self.targets.items(), key=self.priority_key)

    def compute_force_budgeted(self):
        """Find prioritized steering force within the vehicle's budget.

        Returns
        -------
        Point2d: Steering force.
        """
        force = Point2d(0,0)
        owner = self.vehicle
        # If any flocking is active, determine neighbors first
        if self.flocking is True:
            self.flag_neighbor_vehicles(self.flockmates)

        budget = owner.maxforce
        # TODO: Rewrite this to use FORCE_FNC directory??
        for (f, t) in self.priorities:
            # Check if this behaviour is actually active
            # If not, continue to the next behaviour
            status_key = f.func_name[6:].upper()
            if self.status[status_key] is not True:
                continue
            
            newforce = f(owner, *t)
            newnorm = newforce.norm()
            if budget > newnorm:
                # If there is enough force budget left, continue as usual
                force += newforce
                budget -= newnorm
            else:
                # Scale newforce to remaining budget, apply, and exit
                newforce.scale(budget/newnorm)
                force += newforce
                return force

        # If any budget is leftover, just return the total force
        return force

if __name__ == "__main__":
    print("Steering behavior functions. Import this elsewhere. Implemented behaviours are:")
    BEHAVIOUR_LIST.sort()
    print(BEHAVIOUR_LIST)

