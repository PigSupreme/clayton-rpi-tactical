#!/usr/bin/env python
"""A Two-Dimensional Point/Vector Class

There are surely much better implementations of this sort of thing, for
various definitions of 'better.' This module is designed to by easily readable
and portable, without having to fuss with installation/importing of modules
such as numpy that would probably perform better.
"""

# for python3 compat
from __future__ import unicode_literals
from __future__ import absolute_import
from __future__ import print_function

from math import sqrt, acos

class Point2d(object):
    """Creates a 2d vector, defaulting to <0,0>.

    Parameters
    ----------
    x: float
        x-coordinate (defaults to 0).
    y: float
        y-coordinate (defaults to 0).
    """

    def __init__(self, x=0, y=0):
        self.x = float(x)
        self.y = float(y)

    def __str__(self):
        return "Point2d: <%f, %f>" % (self.x, self.y)

    def __neg__(self):
        """Negates each entry; overrides unary - operator.

        Example
        -------
        >>> a = Point2d(1,-2)
        >>> print(-a)
        Point2d: <-1.000000, 2.000000>
        """
        return Point2d(-self.x, -self.y)


    def __add__(self, term):
        """Coordinatewise addition; overrides the + operator.

        Example
        -------
        >>> a = Point2d(1,-2)
        >>> b = Point2d(3,5)
        >>> print(a+b)
        Point2d: <4.000000, 3.000000>
        """
        x = self.x + term.x
        y = self.y + term.y
        return Point2d(x, y)

    def __sub__(self, term):
        """Coordinatewise subtraction; overrides the - operator.

        Example
        -------
        >>> a = Point2d(1,-2)
        >>> b = Point2d(3,5)
        >>> print(a-b)
        Point2d: <-2.000000, -7.000000>
        """
        x = self.x - term.x
        y = self.y - term.y
        return Point2d(x, y)

    def __mul__(self, term):
        """Dot product; overrides the \* operator.

        Example
        -------
        >>> a = Point2d(1,-2)
        >>> b = Point2d(3,5)
        >>> a*b
        -7.0
        """
        return (self.x * term.x) + (self.y * term.y)

    def __getitem__(self, index):
        """Vector components; indexed starting at 0.

        Example
        -------
        >>> a = Point2d(1,-2)
        >>> a[0]
        1.0
        >>> a[1]
        -2.0
        """
        if index == 0:
            return self.x
        elif index == 1:
            return self.y
        raise KeyError("Point2d %s has no component %s" % (self, str(index)))

    def scale(self, scalar):
        """Get a scaled version of this vector.

        Example
        -------
        >>> a = Point2d(1,-2)
        >>> print(a.scale(-2))
        Point2d: <-2.000000, 4.000000>
        """
        x = scalar * self.x
        y = scalar * self.y
        return Point2d(x, y)

    def rotated_by(self, angle, use_deg = False):
        """Get this vector rotated anticlockwise.
        
        Parameters
        ----------
        angle: int or float
            Directed anticlockwise angle to rotate by,
        degrees: boolean
            If True, angle is in degrees. Otherwise radians (default)
        
        
        Example
        -------
        >>> a = Point2d(2,-2)
        >>> print(a.rotated_by(3.14159))
        Point2d: <-1.999995, 2.000005>
        >>> print(a.rotated_by(90,True))
        Point2d: <2.000000, 2.000000>
        """
        if use_deg is True:
            angle = angle / 57.2957795131
        
        c = cos(angle)
        s = sin(angle)
        return Point2d(c*self.x - s*self.y, s*self.x + c*self.y)

    def norm(self):
        """Get the norm (length) of this vector.

        Example
        -------
        >>> a = Point2d(1,-2)
        >>> a.norm()
        2.23606797749979
        """
        return sqrt(self.x**2 + self.y**2)

    def sqnorm(self):
        """Get the squared norm (length) of this vector.

        Example
        -------
        >>> a = Point2d(1,-2)
        >>> a.sqnorm()
        5.0
        """
        return float(self.x**2 + self.y**2)

    def unit(self):
        """Get a unit vector in the same direction as this one.

        Note
        ----
        Be aware of round-off errors; see the example below.

        Example
        -------
        >>> a = Point2d(1,-2)
        >>> print(a.unit())
        Point2d: <0.447214, -0.894427>
        >>> a.unit().norm()
        0.9999999999999999
        """
        return self.scale(1.0/self.norm())

    def normalize(self):
        """Rescale this vector to have length 1.

        Note
        ----
        Be aware of round-off errors; see the example below.

        Example
        -------
        >>> a = Point2d(1,-2)
        >>> a.normalize()
        >>> print(a)
        Point2d: <0.447214, -0.894427>
        >>> a.norm()
        0.9999999999999999
        """
        r = self.norm()
        self.x = float(self.x/r)
        self.y = float(self.y/r)

    def truncate(self, maxlength):
        """Rescale this vector if needed so its length is not too large.

        Parameters
        ----------
        maxlength: float
            Upper limit on the length. If the current length exceeds this,
            the vector will be rescaled.

        Returns
        -------
        bool:
            True if rescaling was done, False otherwise.

        Example
        -------
        >>> a = Point2d(1,-2)
        >>> a.truncate(1.0)
        True
        >>> a = Point2d(-1,2)
        >>> a.truncate(5.0)
        False
        >>> print(a)
        Point2d: <-1.000000, 2.000000>
        >>> a.truncate(1.0)
        True
        >>> print(a)
        Point2d: <-0.447214, 0.894427>
        """
        if self.sqnorm() > maxlength**2:
            r = float(maxlength/self.norm())
            self.x = self.x * r
            self.y = self.y * r
            return True
        else:
            return False

    def angle(self):
        """Get the polar angle of this vector in radians.

        Example
        -------
        >>> a = Point2d(1,-2)
        >>> a.angle()
        -1.1071487177940904

        Notes
        -----
        This is implemeted using acos. Perhaps atan gives better performance?
        """
        theta = acos(self.x/self.norm())
        if self.y < 0:
            theta = -theta
        return float(theta)

    def __div__(self, direction):
        """Length of an orthogonal projection; overrides the / operator.

        Parameters
        ----------
        direction: Point2d
            The vector we project onto; not required to be a unit vector.

        Returns
        -------
        float:
            The length of the projection vector.

        Notes
        -----
        Returns the scalar q such that self = q*v2 + v3, where v2 is in the
        span of direction and v2 and v3 are orthogonal. This is algebraically
        identical to exact division (/).

        If you want the result as a vector, use Point2d.proj(direction) instead.

        Examples
        --------
        >>> a = Point2d(2,2)
        >>> b = Point2d(3,0)
        >>> a/b
        2.0
        >>> b/a
        2.1213203435596424
        """
        # Note: * is the dot product, using __mul__ to override above.
        r = (self*direction)/direction.norm()
        return r

    def proj(self, direction):
        """Get the orthogonal projection of this vector onto another.

        Parameters
        ----------
        direction: Point2d
            The vector we project onto; not required to be a unit vector.

        Returns
        -------
        Point2d
            The unique vector v2 such that self = q*v2 + v3, where v2 is in the
            span of direction and v2 and v3 are orthogonal.

        Example
        -------
        >>> a = Point2d(2,4)
        >>> b = Point2d(3,-2)
        >>> print(a.proj(b))
        Point2d: <-0.461538, 0.307692>
        >>> print(b.proj(a))
        Point2d: <-0.200000, -0.400000>

        Notes
        -----
        If you want both v2 and v3, use Point2d.resolve(direction) instead.
        """
        # Note: * is the dot product, using __mul__ to override above.
        r = (self*direction)/direction.sqnorm()
        proj = direction.scale(r)
        return proj

    def resolve(self, direction):
        """Orthogonal decomposition of this vector in a given direction.

        Parameters
        ----------
        direction: Point2d
            The vector we project onto; not required to be a unit vector.

        Returns
        -------
        (Point2d, Point2d):
            (v2,v3) such that self = q*v2 + v3, where v2 is in the
            span of direction and v2 and v3 are orthogonal.

        Example
        -------
        >>> a = Point2d(2,2)
        >>> b = Point2d(3,0)
        >>> print(a.resolve(b)[0])
        Point2d: <-0.461538, 0.307692>
        >>> print(a.resolve(b)[1])
        Point2d: <2.461538, 3.692308>
        >>> print(a.resolve(b)[0]+a.resolve(b)[1])
        Point2d: <2.000000, 4.000000>
        """
        parallel = self.proj(direction)
        perp = self - parallel
        return (parallel, perp)
        
    def left_normal(self):
        """Returns the left-facing normal of this vector
        
        Example
        -------
        >>> a = Point2d(1, -2)
        >>> print a.left_normal()
        Point2d: <2.000000, 1.000000>
        """
        return Point2d(-self.y, self.x)
    
    def __setitem__(self, index, value):
        """Allows a value to be assigned to each vector components; 
        indexed starting at 0
        
        Example
        -------
        >>> a = Point2d(1, -2)
        >>> print a
        Point2d: <1.000000, -2.000000>
        >>> a[0] = 3
        >>> a[1] = 5
        >>> print a
        Point2d: <3.000000, 5.000000>
        """
        if index == 0:
            self.x = value
        elif index == 1:
            self.y = value
        else:
            raise KeyError("Point2d %s has no component %s" % (self, str(index)))

if __name__ == "__main__":
    a = Point2d(1, -2)
    b = Point2d(3, 20)
    print("a = %s" % a)
    print("b = %s" % b)
    print ("-a = %s" % (-a))
    print("a+b = %s" % str(a+b))
    print("a-b = %s" % str(a-b))
    print("a*b = %s" % str(a*b))
    print("sqrt(2)a = %s" % a.scale(sqrt(2)))
    
    print("a rotated by 90 degrees = %s" % a.rotated_by(90,True))
    print("b rotated by -pi/3 radians = %s" % b.rotated_by(-1.0471975511965976))

    na = a.norm()
    print("||a|| = %s" % na)
    print("||a||^2 = %s" % a.sqnorm())
    print("Unit vector in direction of a: %s, which has norm %s" % (a.unit(),a.unit().norm()))

    a.normalize()
    print("Normalized a = %s" % a)

    aa = a.angle()
    print("Angle of a = %f radians" % aa)
    from math import cos, sin
    print("Rebuilding vector a from norm and angle: <%f,%f>" % (na*cos(aa),na*sin(aa)))

    b.truncate(1)
    print("Truncated b to norm 1: %s" % b)

    projab = a/b
    print("Signed length of projection of a onto b = %f" % projab)
    c = a.proj(b)
    print("Projection of a onto b is %s with length %f" % (c,c.norm()))

    print("Signed length of projection of a onto c = %f" % (a/c))

    cframe = a.resolve(b)
    print("Resolving a in the direction of b...")
    print("Parallel to b: %s" % cframe[0])
    print("Orthogonal to b: %s" % cframe[1])
    print("Checking resolution...")
    print("Dot product of resolved vectors = %f" % (cframe[0]*cframe[1]))
    print("Dot product of b with perpendicular = %f" % (b*cframe[1]))
    print("Sum of resolved vectors = %s" % (cframe[0]+cframe[1]))
    
