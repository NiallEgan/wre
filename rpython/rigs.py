""" Some useful semirings """

class IntRig(object):
    one = 1
    zero = 0

    def mult(self, x, y):
        return x * y

    def plus(self, x, y):
        return x + y

class BoolRig(object):
    one = True
    zero = False

    def mult(self, x, y):
        return x and y

    def plus(self, x, y):
        return x or y

class BitRig(object):
    one = 1
    zero = 0

    def mult(self, x, y):
        return x & y

    def plus(self, x, y):
        return x | y
