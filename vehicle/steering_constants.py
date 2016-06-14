# steering_constants.py
"""
Constants for vehicles and steering behaviours.
"""

########################
## Vehicle2d Defaults ##
########################

POINTMASS2D_MASS = 1.0
POINTMASS2D_MAXSPEED = 5.0
POINTMASS2D_MAXFORCE = 3.5


#######################
## Steering defaults ##
#######################

# Used by FLEE; ignore the point if it's too far away
FLEE_PANIC_SQ = float('inf')

# This contols the gradual deceleration for ARRIVE behavior.
# Larger values will cause more gradual deceleration
ARRIVE_DECEL_TWEAK = 10.0

# Used by EVADE; we ignore the predator if it is too far away.
EVADE_PANIC_SQ = 160**2

# This controls the size of an object detection box for AVOID obstacles
# Length in front of vehicle is 100%-200% of this
AVOID_MIN_LENGTH = 25
# Tweaking constant for braking force of AVOID obstacles
AVOID_BRAKE_WEIGHT = 2.0

# Avoid Walls: Percentage length of side whiskers relative to front whisker
WALLAVOID_WHISKER_SCALE = 0.8

# Take cover: For stalking, set this to cos^2(theta), where theta is the max
# angle from predator's front vector. The stalker will not hide unless within
# this angle of view.
TAKECOVER_STALK_T = 0.1 

# FOLLOW the leader uses ARRIVE with this hesitance, for smooth formations 
FOLLOW_ARRIVE_HESITANCE = 1.5

# For simplicity, we multiply the vehicle's bounding radius by this constant
# to determine the local neighborhood radius for group behaviours.
FLOCKING_RADIUS_MULTIPLIER = 2.0

# Scaling factor for SEPERATE group behaviour.
# Larger values give greater seperation force.
FLOCKING_SEPARATE_SCALE = 1.2

# Cohesion uses ARRIVE with this hesitance, for smooth flocking
FLOCKING_COHESHION_HESITANCE = 3.5
