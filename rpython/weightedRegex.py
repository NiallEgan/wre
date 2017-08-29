""" Implements the 'shifting' algorithm, presented in
    http://sebfisch.github.io/haskell-regexp/regexp-play.pdf for
    weighted regular expressions """

class Expr(object):
    """ Abstract base class """
    _imutable_fields_ = ["rig"]

    def __init__(self, rig):
        """ rig is a semiring with zero, one, plus and mult """
        self._rig = rig
        self._final = self._rig.zero
        self._empty = self._rig.zero

    def final(self):
        """ Returns the weight of the current symbol after being
            processes by the WFA. This value is updated by
            updateFinal
        """
        return self._final

    def reset(self):
        """ Resets the regular expressions """
        self._final = self._rig.zero

    def empty(self):
        """ Returns the weight of the empty string for
            the piece of the regular expression. A getter for
            _empty
        """
        return self._empty


class Sym(Expr):
    """ A literal symbol in the regex """
    _imutable_fields_ = ["weightFunction", "tag", "_empty"]

    def __init__(self, weightFunction, rig, tag=""):
        Expr.__init__(self, rig)
        self.weightFunction = weightFunction  # A function from the alphabet to the rig
        self.mark = self._rig.zero
        self.tag = tag

    def shift(self, mark, symbol):
        self.mark = self._rig.mult(mark, self.weightFunction.call(symbol))

    def updateFinal(self):
        self._final = self.mark
        return self._final

    def copy(self):
        return Sym(self.weightFunction, self._rig, self.tag)

    def reset(self):
        self._final = self._rig.zero
        self.mark = self._rig.zero


class Eps(Expr):
    """ A null string in the regex """

    _imutable_fields_ = ["rig", "_empty"]
    def __init__(self, rig):
        Expr.__init__(self, rig)
        self._empty = self._rig.one

    def shift(self, mark, symbol):
        return self

    def updateFinal(self):
        return self._final  # Value is always one

    def copy(self):
        return Eps(self._rig)


class Rep(Expr):
    """ Repetiton: exp repeated zero or more times """

    _imutable_fields_ = ["rig", "_empty", "exp"]
    def __init__(self, exp, rig):
        Expr.__init__(self, rig)
        self.exp = exp
        self._empty = self._rig.one

    def shift(self, mark, symbol):
        self.exp.shift(self._rig.plus(mark, self._final), symbol)

    def updateFinal(self):
        self._final = self.exp.updateFinal()
        return self._final

    def copy(self):
        return Rep(self.exp.copy(), self._rig)

    def reset(self):
        self.exp.reset()
        self._final = self._rig.zero

class Plus(Expr):
    """ exp repeated one or more times """

    _imutable_fields_ = ["rig", "_empty", "exp"]
    def __init__(self, exp, rig):
        Expr.__init__(self, rig)
        self.exp = exp
        self._empty = self.exp.empty()

    def shift(self, mark, symbol):
        self.exp.shift(self._rig.plus(mark, self._final), symbol)

    def updateFinal(self):
        self._final = self.exp.updateFinal()
        return self._final

    def copy(self):
        return Plus(self.exp.copy(), self._rig)

    def reset(self):
        self.exp.reset()
        self._final = self._rig.zero

class Question(Expr):
    """ exp 1 or 0 times """

    _imutable_fields_ = ["rig", "_empty", "exp"]
    def __init__(self, exp, rig):
        Expr.__init__(self, rig)
        self.exp = exp
        self._empty = self._rig.one

    def shift(self, mark, symbol):
        self.exp.shift(mark, symbol)

    def updateFinal(self):
        self._final = self.exp.updateFinal()
        return self._final

    def copy(self):
        return Question(self.exp.copy(), self._rig)

    def reset(self):
        self.exp.reset()
        self._final = self._rig.zero

class Branch(Expr):
    """ A superclass for binary operators """

    _imutable_fields_ = ["rig", "_empty", "left", "right"]
    def __init__(self, left, right, rig, tag=""):
        Expr.__init__(self, rig)
        self.left = left
        self.right = right
        self.tag = tag

    def reset(self):
        self.left.reset()
        self.right.reset()
        self._final = self._rig.zero

class Seq(Branch):
    """ Concatanation: match left and right """

    def __init__(self, left, right, rig):
        Branch.__init__(self, left, right, rig)
        self._empty = self._rig.mult(self.left.empty(), self.right.empty())

    def shift(self, mark, symbol):
    #    print(symbol)
        self.left.shift(mark, symbol)
        self.right.shift(self._rig.plus(
                         self._rig.mult(mark, self.left.empty()),
                         self.left.final()), symbol)

    def updateFinal(self):
        l = self.left.updateFinal()
        r = self.right.updateFinal()
        self._final = self._rig.plus(self._rig.mult(l, self.right.empty()), r)
        return self._final

    def copy(self):
        return Seq(self.left.copy(), self.right.copy(), self._rig)

class Alt(Branch):
    """ Alternation: match left or right """

    def __init__(self, left, right, rig):
        Branch.__init__(self, left, right, rig)
        self._empty = self._rig.plus(self.left.empty(), self.right.empty())

    def shift(self, mark, symbol):
        self.left.shift(mark, symbol)
        self.right.shift(mark, symbol)

    def updateFinal(self):
        l = self.left.updateFinal()
        r = self.right.updateFinal()
        self._final = self._rig.plus(l, r)
        return self._final

    def copy(self):
        return Alt(self.left.copy(), self.right.copy(), self._rig)
