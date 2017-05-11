# steering_constants.py
"""
Default values of constants for vehicles and steering behaviours.
"""

from __future__ import print_function

########################
## Vehicle2d Defaults ##
########################

#: Vehicle mass for rectilinear motion.
POINTMASS2D_MASS = 1.0
#: Maximum vehicle speed per rectilinear motion update.
POINTMASS2D_MAXSPEED = 5.0
#: Maximum force/budget per rectilinear motion update.
POINTMASS2D_MAXFORCE = 3.5

#: Rotational Inertia for rigid-body physics
RIGIDBODY2D_INERTIA = 1.0
#: Maximum angular velocity per rigid-body update.
RIGIDBODY2D_MAXOMEGA = 90.0
#: Maximum torque per rigid-body update.
RIGIDBODY2D_MAXTORQUE = 75.0

#######################
## Steering defaults ##
#######################

#: Used by FLEE; ignore the point if it's too far away
FLEE_PANIC_SQ = float('inf')

#: This contols the gradual deceleration for ARRIVE behavior.
#: Larger values will cause more gradual deceleration.
ARRIVE_DECEL_TWEAK = 10.0

#: Used by EVADE; we ignore the predator if it is too far away.
EVADE_PANIC_SQ = 160**2

#: This controls the size of an object detection box for AVOID obstacles.
#: Length in front of vehicle is 100%-200% of this.
AVOID_MIN_LENGTH = 25

#: Tweaking constant for braking force of AVOID obstacles.
AVOID_BRAKE_WEIGHT = 2.0

#: WALLAVOID: Proportional length of side whiskers relative to front whisker.
WALLAVOID_WHISKER_SCALE = 0.8

#: TAKECOVER: For stalking, set this to cos^2(theta), where theta is the max
#: angle from target's front vector. The stalker will not hide unless within
#: this angle of view.
TAKECOVER_STALK_T = 0.1

#: FOLLOW the leader uses ARRIVE with this hesitance, for smooth formations.
FOLLOW_ARRIVE_HESITANCE = 1.5

#: SteeringPath will treat consecutive waypoints that are closer than this
#: as duplicates, and remove them from the path.
PATH_EPSILON_SQ = 10.0**2

#: Used by PATHFOLLOW/RESUME to determine when we're close enough to a waypoint.
WAYPOINT_TOLERANCE_SQ = 10.0**2

#: Exponential decay constant for PATHRESUME.
PATHRESUME_DECAY = 0.075

#: For simplicity, we multiply the vehicle's bounding radius by this constant
#: to determine the local neighborhood radius for group behaviours.
FLOCKING_RADIUS_MULTIPLIER = 2.0

#: Scaling factor for SEPERATE group behaviour.
#: Larger values give greater seperation force.
FLOCKING_SEPARATE_SCALE = 1.2

#: Cohesion uses ARRIVE with this hesitance, for smooth flocking.
FLOCKING_COHESHION_HESITANCE = 3.5

#: This to avoids the need for import * ...work in progress.
BASEPOINTMASS2D_DEFAULTS = {
        'MASS': POINTMASS2D_MASS,
        'MAXSPEED': POINTMASS2D_MAXSPEED,
        'MAXFORCE': POINTMASS2D_MAXFORCE,
        'INERTIA':  RIGIDBODY2D_INERTIA,
        'MAXOMEGA': RIGIDBODY2D_MAXOMEGA,
        'MAXTORQUE': RIGIDBODY2D_MAXTORQUE
        }

if __name__ == "__main__":
    print("Steering constants. Import this elsewhere.")
