# vehicle2d.py
"""Module containing Vehicle class, for use with Pygame."""

# for python3 compat
from __future__ import unicode_literals
from __future__ import absolute_import
from __future__ import print_function
from __future__ import division

import os, sys, pygame
from pygame.locals import RLEACCEL, QUIT, MOUSEBUTTONDOWN

POINTMASS2D_MASS = 5
POINTMASS2D_MAXSPEED = 50000
POINTMASS2D_MAXFORCE = 10000
DAMPING_COEFF = 10
SPRING_CONST = 3
MUSCLE_K = 70
SOLIDS_K = 100
CROSS_K = 150
FISH = True
FREQ = 225
SQUEEZE = 0.88

UPDATE_SPEED = 0.02

from random import randint

INF = float('inf')

# TODO: Adjust this depending on where this file ends up.
sys.path.extend(['../vpoints', '../vehicle'])
from point2d import Point2d

# Point2d functions return radians, but pygame wants degrees. The negative
# is needed since y coordinates increase downwards on screen. Multiply a
# math radians result by SCREEN_DEG to get pygame screen-appropriate degrees.
SCREEN_DEG = -57.2957795131

# A PointMass has its heading aligned with velocity. However, if the speed is
# almost zero (squared speed is below this threshold), we skip alignment in
# order to avoid jittery behaviour.
SPEED_EPSILON = .000000001

def load_pygame_image(name, colorkey=None):
    """Loads image from current working directory for use in pygame.

    Parameters
    ----------
    name: string
        Image file to load (must be pygame-compatible format)
    colorkey: pygame.Color
        Used to set a background color for this image that will be ignored
        during blitting. If set to -1, the upper-left pixel color will be
        used as the background color. See pygame.Surface.set_colorkey() for
        further details.

    Returns
    -------
    (pygame.Surface, pygame.rect):
        For performance reasons, the returned Surface is the same format as
        the pygame display. The alpha channel is removed.

    Note
    ----
    TODO: This function is imported by the demos, but perhaps there is a
    better location for it?

    """
    imagefile = os.path.join(os.getcwd(), name)
    try:
        image_surf = pygame.image.load(imagefile)
    except pygame.error as message:
        print('Error: Cannot load image file: %s' % name)
        print('Current working directory is: %s' % os.getcwd())
        raise SystemExit(message)

    # This converts the surface for maximum blitting performance,
    # including removal of any alpha channel:
    image_surf = image_surf.convert()

    # This sets the background (ignored during blit) color:
    if colorkey is not None:
        if colorkey is -1:
            colorkey = image_surf.get_at((0,0))
        image_surf.set_colorkey(colorkey, RLEACCEL)
    return image_surf, image_surf.get_rect()




class PointMass2dSprite(pygame.sprite.Sprite):
    """A Pygame sprite used to display a BasePointMass2d object."""

    def __init__(self, owner, img_surf, img_rect):
        # Must call pygame's Sprite.__init__ first!
        pygame.sprite.Sprite.__init__(self)

        self.owner = owner

        # Pygame image information for blitting
        self.orig = img_surf
        self.image = img_surf
        self.rect = img_rect

    def update(self, delta_t=1.0):
        """Called by pygame.Group.update() to redraw this sprite."""
        owner = self.owner
        # Update position
        self.rect.center = owner.pos[0], owner.pos[1]
        # Rotate for blitting
        theta = owner.front.angle()*SCREEN_DEG
        center = self.rect.center
        self.image = pygame.transform.rotate(self.orig, theta)
        self.rect = self.image.get_rect()
        self.rect.center = center

class BasePointMass2d(object):
    """A moving object with rectilinear motion and optional sprite.

    Parameters
    ----------
    position: Point2d
        Center of mass, in screen coordinates.
    radius: float
        Bounding radius of the object.
    velocity: Point2d
        Velocity vector, in screen coordinates. Initial facing matches this.
    spritedata: list or tuple, optional
        Extra data used to create an associate sprite. See notes below.

    Notes
    -----
    This provides a minimal base class for a pointmass with bounding radius
    and heading aligned to velocity. Use move() for physics updates each
    cycle (including applying force).

    As we typically will be rendering these objects within some environment,
    the constructor provides an optional spritedata parameter that can be used
    to create an associated sprite. This is currently implemented using the
    PointMass2dSprite class above (derived from pygame.sprite.Sprite), but
    can be overridden by changing the _spriteclass attribute.
    """
    _spriteclass = PointMass2dSprite
    """Default sprite class to use for rendering."""

    def __init__(self, position, radius, velocity, spritedata=None):
        # Basic object physics
        # Note: We can't use self.pos = position here because of Point2d's
        # __init__ method (and lack of __copy__), ditto for self.vel.
        self.pos = Point2d(position[0], position[1])  # Center of object
        self.radius = radius                          # Bounding radius
        self.vel = Point2d(velocity[0], velocity[1])  # Current Velocity

        # Normalized front vector in world coordinates.
        # This stays aligned with the object's velocity (using move() below)
        try:
            self.front = velocity.unit()
        except ZeroDivisionError:
            # If velocity is <0,0>, set facing to screen upwards
            self.front = Point2d(0,-1)
        self.left = Point2d(-self.front[1], self.front[0])

        # Movement constraints (defaults from steering_constants.py)
        ## TODO: Put these in the function argument, perhaps as **kwargs
        self.mass = POINTMASS2D_MASS
        self.maxspeed = POINTMASS2D_MAXSPEED
        self.maxforce = POINTMASS2D_MAXFORCE

        if spritedata is not None:
            self.sprite = PointMass2dSprite(self, *spritedata)

    def move(self, delta_t=1.0, force_vector=None):
        """Updates position, velocity, and acceleration.

        Parameters
        ----------
        delta_t: float
            Time increment since last move.
        force_vector: Point2d, optional
            Constant force during for this update.
        """
        # Update position using current velocity
        self.pos = self.pos + self.vel.scale(delta_t)

        # Apply force, if any...
        if force_vector:
            # Don't exceed our maximum force; compute acceleration/velocity
            force_vector.truncate(self.maxforce)
            accel = force_vector.scale(delta_t/self.mass)
            self.vel = self.vel + accel
        # ..but don't exceed our maximum speed
        self.vel.truncate(self.maxspeed)

        # Align heading to match our forward velocity. Note that
        # if velocity is very small, skip this to avoid jittering.
        if self.vel.sqnorm() > SPEED_EPSILON:
            self.front = self.vel.unit()
            self.left = Point2d(-self.front[1], self.front[0])


class SpringMass2d(BasePointMass2d):
    """A point mass that can accumulate several forces and apply all at once.
    
    TODO: Rename this to something more general.
    """
    
    def __init__(self, position, mass, velocity, spritedata=None):
        radius = 5
        BasePointMass2d.__init__(self, position, radius, velocity, spritedata)
        self.mass = mass
        self.accumulated_force = Point2d(0,0)
        
    def accumulate_force(self, force_vector):
        """Add a new force to what's already been acculumated."""
        self.accumulated_force = self.accumulated_force + force_vector
        
    def apply_force(self, delta_t=1.0):
        # Compute damping force
        force = self.accumulated_force - self.vel.scale(DAMPING_COEFF)
        
        self.move(delta_t, force)
        self.accumulated_force = Point2d(0,0)
        

class IdealSpring2d(BasePointMass2d):
    """An ideal (massless, stiff) spring attaching two point masses.
    
    Parameters
    ----------
    spring_constant: positive float
        Linear Spring Constant (Hooke's Law).
    rest_length: positive float
        Natural/rest lenght of this spring.
    mass1: BasePointMass2d
        Point mass at the base of this spring; see Notes
    mass2: BasePointMass2d
        Point mass at the end of this spring; see Notes
    
    Notes
    -----
    
    Since spring physics use vectors, the spring needs an implicit orientation
    (from mass1 to mass2). This orientation is used internally, but has no
    visible effect outside of the exert_force update.
    """

    def __init__(self, spring_constant, rest_length, mass1, mass2):
        self.k = spring_constant
        # Give negative rest_length to use current distance between masses
        if rest_length < 0:
            self.natlength = (mass1.pos - mass2.pos).norm()
        else:
            self.natlength = rest_length
        self.minlength = SQUEEZE*self.natlength
        self.squeeze = 0
        self.mass_base = mass1
        self.mass_tip = mass2
        
    def exert_force(self):
        """Compute spring force and and apply it to the attached masses."""
        self.displacement = self.mass_tip.pos - self.mass_base.pos
        self.curlength = self.displacement.norm()
        
        # Compute desired length (from squeeze)
        target_length = self.natlength + self.squeeze*(self.minlength - self.natlength)        
        
        self.curscale = target_length/self.curlength
        magnitude = self.k*(1 - self.curscale)
        self.mass_base.accumulate_force(self.displacement.scale(magnitude))
        self.mass_tip.accumulate_force(self.displacement.scale(-magnitude))


if __name__ == "__main__":
    pygame.init()

    # Display constants
    size = sc_width, sc_height = 800, 640
    screen = pygame.display.set_mode(size)
    pygame.display.set_caption('Spring-mass demo')
    bgcolor = 111, 145, 192

    # Fish coordinate nodes
    MASS_SCALE = 12
    SIZE_SCALE = 5
    nodedata = [(0,0,1.1), (65,0,0.0995)]  # Head and tail
    for i, j, m in [(8,4,6.6), (20,6,11.0), (35,6,8.6), (47,4,1.1), (57,2,1.1)]:
        nodedata.append((i,j,m*MASS_SCALE))
        nodedata.append((i,-j,m*MASS_SCALE))
    numnodes = len(nodedata)
    img = list(range(numnodes))
    rec = list(range(numnodes))
        
    # Node Sprites
    obj = []
    img = []
    rec = []
    for i, j, m in nodedata:
        imgt, rect = load_pygame_image('../images/node.png', -1)
        img.append(imgt)
        rec.append(rect)
        nodet = SpringMass2d(Point2d(i+50,j+75).scale(SIZE_SCALE), m , Point2d(0,0), (imgt, rect))
        obj.append(nodet)
        
    # List of nodes only, for later use
    nodelist = obj[:]
    rgroup = [node.sprite for node in obj]
    
    # Set-up pygame rendering for all objects
    allsprites = pygame.sprite.RenderPlain(rgroup)

    # Set up springs
    springs = []
    edge_muscles = [(2,4), (4,6), (6,8), (3,5), (5,7), (7,9)]
    muscle_k = MUSCLE_K
    for edge in edge_muscles:
        i, j = edge
        springs.append(IdealSpring2d(muscle_k, -1, nodelist[i], nodelist[j]))
    muscle_count = len(springs)
        
    edge_solids = [(0,2), (0,3), (2,3), (4,5), (6,7), (8,9), (10,11), (8,10), (10,1), (9,11), (11,1)]
    solids_k = SOLIDS_K
    for edge in edge_solids:
        i, j = edge
        springs.append(IdealSpring2d(solids_k, -1, nodelist[i], nodelist[j]))
        
    edge_cross = [(2,5), (3,4), (4,7), (5,6), (6,9), (7,8), (9,10), (8,11)]
    cross_k = CROSS_K
    for edge in edge_cross:
        i, j = edge
        springs.append(IdealSpring2d(cross_k, -1, nodelist[i], nodelist[j]))
    
    ############  Main Loop  ######################

    freq = FREQ
    ticks = 0
    ticks2 = freq//2
    springs[1].squeeze = 1
    springs[4].squeeze = 0
    
    springs[2].squeeze = 0
    springs[5].squeeze = 1
    
    while 1:
        for event in pygame.event.get():
            if event.type in [QUIT, MOUSEBUTTONDOWN]:
                pygame.quit()
                sys.exit()

        # Squeeze Test
        if ticks >= freq:
            ticks = 0
            for i in [1,4]:
                springs[i].squeeze = 1 - springs[i].squeeze 
        
        if ticks2 >= freq:
            ticks2 = 0
            for i in [2,5]:
                springs[i].squeeze = 1 - springs[i].squeeze 


        # Update Spring Forces
        for spring in springs:
            spring.exert_force()

        # Update Nodes
        for node in nodelist:
            node.apply_force(UPDATE_SPEED)

        # Shift sprites so that node 0 stays fixed
#        ref_pos = nodelist[0].pos
#        for node in nodelist:
#            node.pos = node.pos - ref_pos + Point2d(sc_width/4, sc_height/2)            

        # Update Sprites (via pygame sprite group update)
        allsprites.update(UPDATE_SPEED)

        # Render
        screen.fill(bgcolor)

        # Manually render each spring
        for spring in springs:
            scale = spring.curscale
            if scale > 1:
                spcolor = min(255, 64*scale), 0, 0
            else:
                spcolor = 0, min(255, 64//scale), 0
            start = spring.mass_base.pos.ntuple()
            stop = spring.mass_tip.pos.ntuple()
            pygame.draw.line(screen, spcolor, start, stop, 2)

        # Render regular sprites (point masses)
        allsprites.draw(screen)            
        pygame.display.flip()
        ticks = ticks + 1

        #pygame.time.delay(2)

    # Clean-up here
    pygame.time.delay(2000)