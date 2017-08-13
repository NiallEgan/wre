""" Implements the 'shifting' algorithm, presented in
    http://sebfisch.github.io/haskell-regexp/regexp-play.pdf for
    weighted regular expressions """

class Expr(object):
    def __init__(self, rig):
        """ rig is a semiring with zero, one, plus and mult """
        self._final = rig.zero
        self._rig = rig

    def final(self):
        return self._final


class Sym(Expr):
    """ A literal symbol in the regex """

    def __init__(self, weightFunction, rig, tag=""):
        super(Sym, self).__init__(rig)
        self.weightFunction = weightFunction  # A function from the alphabet to the rig
        self.mark = self._rig.zero
        self._empty = self._rig.zero
        self.tag = tag

    def shift(self, mark, symbol):
        self.mark = self._rig.mult(mark, self.weightFunction(symbol))
    #    print(self.tag, self.weightFunction(symbol), symbol)
        return self

    def empty(self):
        return self._empty  # This value will never change

    def updateFinal(self):
        self._final = self.mark

class Eps(Expr):
    """ A null string in the regex """

    def __init__(self, rig):
        super(Eps, self).__init__(rig)
        self._empty = self._rig.one

    def shift(self, mark, symbol):
        return self

    def empty(self):
        return self._empty

    def updateFinal(self):
        pass  # value never changes


class Rep(Expr):
    """ Repetiton: exp repeated zero or more times """

    def __init__(self, exp, rig):
        super(Rep, self).__init__(rig)
        self.exp = exp
        self._empty = self._rig.one

    def shift(self, mark, symbol):
        self.exp.shift(self._rig.plus(mark, self._final), symbol)

    def empty(self):
        return self._empty

    def updateFinal(self):
        self.exp.updateFinal()
        self._final = self.exp.final()

class Plus(Expr):
    """ exp repeated one or more times """

    def __init__(self, exp, rig):
        super(Plus, self).__init__(rig)
        self.exp = exp
        self._empty = None

    def shift(self, mark, symbol):
        self.exp.shift(self._rig.plus(mark, self._final), symbol)

    def empty(self):
        if self._empty is None:
            self._empty = self.exp.empty()
        return self._empty

    def updateFinal(self):
        self.exp.updateFinal()
        self._final = self.exp.final()

class Question(Expr):
    """ exp 1 or 0 times """

    def __init__(self, exp, rig):
        super(Question, self).__init__(rig)
        self.exp = exp
        self._empty = self._rig.one

    def shift(self, mark, symbol):
        self.exp.shift(mark, symbol)

    def empty(self):
        return self._empty

    def updateFinal(self):
        self.exp.updateFinal()
        self._final = self.exp.final()

class Branch(Expr):
    """ A superclass for binary operators """

    def __init__(self, left, right, rig):
        super(Branch, self).__init__(rig)
        self.left = left
        self.right = right
        self._empty = None

class Seq(Branch):
    """ Concatanation: match left and right """

    def __init__(self, left, right, rig):
        super(Seq, self).__init__(left, right, rig)

    def shift(self, mark, symbol):
    #    print(symbol)
        self.left.shift(mark, symbol)
        self.right.shift(self._rig.plus(
                         self._rig.mult(mark, self.left.empty()),
                         self.left.final()), symbol)

    def empty(self):
        if self._empty is None:  # This needs only be computed once,
            # cache for later use
            self._empty = self._rig.mult(self.left.empty(), self.right.empty())
        return self._empty

    def updateFinal(self):
        self.left.updateFinal()
        self.right.updateFinal()
        self._final = self._rig.plus(self._rig.mult(self.left.final(), self.right.empty()),
                                     self.right.final())

class Alt(Branch):
    """ Alternation: match left or right """

    def __init__(self, left, right, rig):
        super(Alt, self).__init__(left, right, rig)

    def shift(self, mark, symbol):
        self.left.shift(mark, symbol)
        self.right.shift(mark, symbol)

    def empty(self):
        if self._empty is None:
            self._empty = self._rig.plus(self.left.empty(), self.right.empty())
        return self._empty

    def updateFinal(self):
        self.left.updateFinal()
        self.right.updateFinal()
        self._final = self._rig.plus(self.left.final(), self.right.final())

def match(r, string, rig):
    """ Returns if string matches the regex r """

    if string == "":
        return r.empty()

    r.shift(rig.one, string[0])  # Want to shift in an initial mark to start the
    # NFA

    for c in string[1:]:
        r.updateFinal()  # Explicitly call update here, cache the values
        r.shift(rig.zero, c)

    r.updateFinal()
    return r.final()
