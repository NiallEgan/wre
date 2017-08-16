""" Implements the 'shifting' algorithm, presented in
    http://sebfisch.github.io/haskell-regexp/regexp-play.pdf for
    weighted regular expressions """

class Expr(object):
    _imutable_fields_ = ["rig"]
    def __init__(self, rig):
        """ rig is a semiring with zero, one, plus and mult """
        self._final = rig.zero
        self._rig = rig

    def final(self):
        return self._final


class Sym(Expr):
    """ A literal symbol in the regex """

    _imutable_fields_ = ["weightFunction", "rig", "tag", "_empty"]
    def __init__(self, weightFunction, rig, tag=""):
        Expr.__init__(self, rig)
        self.weightFunction = weightFunction  # A function from the alphabet to the rig
        self.mark = self._rig.zero
        self._empty = self._rig.zero
        self.tag = tag

    def shift(self, mark, symbol):
        self.mark = self._rig.mult(mark, self.weightFunction.call(symbol))

    def empty(self):
        return self._empty  # This value will never change

    def updateFinal(self):
        self._final = self.mark

    def copy(self):
        return Sym(self.weightFunction, self._rig, self.tag)

class Eps(Expr):
    """ A null string in the regex """

    _imutable_fields_ = ["rig", "_empty"]
    def __init__(self, rig):
        Expr.__init__(self, rig)
        self._empty = self._rig.one

    def shift(self, mark, symbol):
        return self

    def empty(self):
        return self._empty

    def updateFinal(self):
        pass  # value never changes

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

    def empty(self):
        return self._empty

    def updateFinal(self):
        self.exp.updateFinal()
        self._final = self.exp.final()

    def copy(self):
        return Rep(self.exp.copy(), self._rig)

class Plus(Expr):
    """ exp repeated one or more times """

    _imutable_fields_ = ["rig", "_empty", "exp"]
    def __init__(self, exp, rig):
        Expr.__init__(self, rig)
        self.exp = exp
        self._empty = self.exp.empty()

    def shift(self, mark, symbol):
        self.exp.shift(self._rig.plus(mark, self._final), symbol)

    def empty(self):
        return self._empty

    def updateFinal(self):
        self.exp.updateFinal()
        self._final = self.exp.final()

    def copy(self):
        return Plus(self.exp.copy(), self._rig)

class Question(Expr):
    """ exp 1 or 0 times """

    _imutable_fields_ = ["rig", "_empty", "exp"]
    def __init__(self, exp, rig):
        Expr.__init__(self, rig)
        self.exp = exp
        self._empty = self._rig.one

    def shift(self, mark, symbol):
        self.exp.shift(mark, symbol)

    def empty(self):
        return self._empty

    def updateFinal(self):
        self.exp.updateFinal()
        self._final = self.exp.final()

    def copy(self):
        return Question(self.exp.copy(), self._rig)

class Branch(Expr):
    """ A superclass for binary operators """

    _imutable_fields_ = ["rig", "_empty", "left", "right"]
    def __init__(self, left, right, rig):
        Expr.__init__(self, rig)
        self.left = left
        self.right = right

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

    def empty(self):
        return self._empty

    def updateFinal(self):
        self.left.updateFinal()
        self.right.updateFinal()
        self._final = self._rig.plus(self._rig.mult(self.left.final(), self.right.empty()),
                                     self.right.final())

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

    def empty(self):
        return self._empty

    def updateFinal(self):
        self.left.updateFinal()
        self.right.updateFinal()
        self._final = self._rig.plus(self.left.final(), self.right.final())

    def copy(self):
        return Alt(self.left.copy(), self.right.copy(), self._rig)
