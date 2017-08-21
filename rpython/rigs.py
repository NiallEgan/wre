""" Due to the limitations of static typing, all rigs have to act in
    [(Int, Int)]  """

# Some wrappers for type conversion

def toInt(f):
    def wrapper(self, x, y):
        return [(f(self, x[0][0], y[0][0]), 0)]

    return wrapper

def toTuple(f):
    def wrapper(self, x, y):
        return [f(self, x[0], y[0])]

    return wrapper

class Rig(object):
    one = [(0, 0)]
    zero = [(0, 0)]

    def mult(self, x, y):
        return self.one

    def plus(self, x, y):
        return self.one

class IntRig(Rig):
    one = [(1, 0)]
    zero = [(0, 0)]

    @toInt
    def mult(self, x, y):
        return x * y

    @toInt
    def plus(self, x, y):
        return x + y

""" Issue: As RPython does not support static polymorphism, it is non-trivial
    to add support for multiple rigs (at least with different typed ones and zeroes)
    Possible solutions:
    1. Somehow build in support for static polymorphism - very difficult
    2. Except that the program will be fundamentally limited. Pick a set of functions
       which the program should be able to perform, use the most complex type necessary
       everywhere. - ugly, limits the program intrinsically.

"""
"""
class _BoolRig(_Rig):
    def __init__(self, one, zero):
        _Rig.__init__(self, one, zero)

    @fromToZ2
    def mult(self, x, y):
        return x and y

    @fromToZ2
    def plus(self, x, y):
        return x or y

boolRig = _BoolRig(True, False)
"""

class BitRig(Rig):
    one = [(1, 0)]
    zero = [(0, 0)]

    @toInt
    def mult(self, x, y):
        return x & y

    @toInt
    def plus(self, x, y):
        return x | y

class PositionRig(Rig):
    """
     zero = (2, 0) : Non matching character
     one = (1, 0)   : A matching, but non starting character
     Other elements will be of the form (0, n) where n is the
     index of the char
    """

    one = [(1, 0)]
    zero = [(2, 0)]

    @toTuple
    def mult(self, x, y):
        if x[0] == 2 or y[0] == 2:
            return self.zero[0]  # Just zero really, but will get wrapped
        elif x[0] == 1:
            return y
        else:
            return x

    @toTuple
    def plus(self, x, y):  # Reperesenting an alternation
        # RPython doesn't support min for tuples...
        if x[0] < y[0]:
            return x
        elif x[0] > y[0]:
            return y
        elif x[1] < y[1]:
            return x
        else:
            return y
