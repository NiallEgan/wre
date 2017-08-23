""" Due to the limitations of static typing, all rigs have to act in
    [(Int, Int)]  """

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

class IntRig(Rig):
    one = (1, 0)
    zero = (0, 0)

    @toInt
    def mult(self, x, y):
        return x * y

    @toInt
    def plus(self, x, y):
        return x + y

class BitRig(Rig):
    one = (1, 0)
    zero = (0, 0)

    @toInt
    def mult(self, x, y):
        return x & y

    @toInt
    def plus(self, x, y):
        return x | y

class StartPositionRig(Rig):
    """
     zero = (2, 0) : Non matching character, which causes the whole match to fail
     one = (1, 0)   : A non matching character, but not causing a match to fail
     Other elements will be of the form (0, n) where n is the
     index of the char
    """

    one = (1, 0)
    zero = (2, 0)

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

class StartEndPositionRig(Rig):
    """ Multiply : (x, y) * (a, b) = (x, b) """

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
        if x == self.zero:
            return y
        elif y == self.zero:
            return x
        elif x == self.one:
            return y
        elif y == self.one:
            return x
        else:
            if x[0] < y [0]:  # Leftmost first
                return x
            elif y[0] < x[0]:
                return y
            elif x[1] < y[1]:  # Then longest
                return y
            else:
                return x
