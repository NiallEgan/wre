""" Some useful semirings. Due to the limitations of static currently typing, all rigs have to act in
    (Int, Int).  """

# Some wrappers for type conversion

def toInt(f):
    def wrapper(self, x, y):
        return (f(self, x[0], y[0]), 0)

    return wrapper

class Rig(object):
    one = (0, 0)
    zero = (0, 0)

    def mult(self, x, y):
        return self.one

    def plus(self, x, y):
        return self.one

    def autoMatch(self, sym):
        # Shouldn't really be part of the rigs, but necessary
        return self.one

class IntRig(Rig):
    """ Simple Z+ semiring """

    one = (1, 0)
    zero = (0, 0)

    @toInt
    def mult(self, x, y):
        return x * y

    @toInt
    def plus(self, x, y):
        return x + y

class BitRig(Rig):
    """ Basically the boolean semiring, but rather than use
        bools (which have shortcircuting operators) use bits
        instead
    """

    one = (1, 0)
    zero = (0, 0)

    @toInt
    def mult(self, x, y):
        return x & y

    @toInt
    def plus(self, x, y):
        return x | y

class StartPositionRig(Rig):
    """ A rig that will find the start of the leftmost, longest match
        zero = (-2, 0) : Non matching character, which causes the whole match to fail
        one = (-1, 0) : A non matching character, but not causing a match to fail
        Other elements will be of the form (0, n) where n is the
        index of the character matched.
    """

    one = (-1, 0)
    zero = (-2, 0)

    def mult(self, x, y):  # Reperesenting a concatanation
        if x == self.zero or y == self.zero:
            return self.zero
        elif x == self.one:
            return y
        else:
            return x

    def plus(self, x, y):  # Reperesenting an alternation
        if x == self.zero:
            return y
        elif y == self.zero:
            return x
        elif x == self.one:
            return y
        elif y == self.one:
            return x
        else:
            return (0, min(x[1], y[1]))

    def autoMatch(self, sym):
        return (0, sym[0])

class StartEndPositionRig(Rig):
    """ A rig that finds the start of the end of the leftmost
        longest match.
            Multiply: (x, y) * (a, b) = (x, b) - concatanate matches
            Plus: pick the longest leftmost match
    """

    one = (-1, -1)
    zero = (-2, -2)

    def mult(self, x, y):  # Reperesenting a concatanation
        if x == self.zero or y == self.zero:
            return self.zero
        elif x == self.one:
            return y
        elif y == self.one:
            return x
        else:
            return (x[0], y[1])

    def plus(self, x, y):  # Reperesenting an alternation
        if x == self.zero or y != self.zero and x == self.one or (y[0] >= 0 and y[0] < x[0] or x[0] == y[0] and y[1] > x[1]):
            return y
        else:  # Fewer branches => faster JIT
            return x

    def autoMatch(self, sym):
        return (sym[0], sym[0])
