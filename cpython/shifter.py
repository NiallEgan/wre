""" Implements the 'shifting' algorithm, presented in
    http://sebfisch.github.io/haskell-regexp/regexp-play.pdf """

from regexRepr import regexToPost

class Expr(object):
    """ Base class for regex symbols """

    def __init__(self):
        self._final = False

    def final(self):
        return self._final

class Sym(Expr):
    """ A literal symbol in the regex """

    def __init__(self, symbol):
        super(Sym, self).__init__()
        self.symbol = symbol
        self.mark = False
        self._empty = False

    def shift(self, mark, symbol):
        self.mark = mark and symbol == self.symbol
        return self

    def empty(self):
        return self._empty  # This value will never change

    def updateFinal(self):
        self._final = self.mark

class Eps(Expr):
    """ A null string in the regex """

    def __init__(self):
        super(Eps, self).__init__()
        self._empty = True

    def shift(self, mark, symbol):
        return self

    def empty(self):
        return self._empty

    def updateFinal(self):
        pass  # value never changes


class Rep(Expr):
    """ Repetiton: exp repeated zero or more times """

    def __init__(self, exp):
        super(Rep, self).__init__()
        self.exp = exp
        self._empty = True

    def shift(self, mark, symbol):
        self.exp.shift(mark or self.exp.final(), symbol)

    def empty(self):
        return self._empty

    def updateFinal(self):
        self.exp.updateFinal()
        self._final = self.exp.final()

class Branch(Expr):
    """ A superclass for binary operators """

    def __init__(self, left, right):
        super(Branch, self).__init__()
        self.left = left
        self.right = right
        self._empty = None

class Seq(Branch):
    """ Concatanation: match left and right """

    def __init__(self, left, right):
        super(Seq, self).__init__(left, right)

    def shift(self, mark, symbol):
        oldFinal = self.left.final()
        self.left.shift(mark, symbol)
        self.right.shift((mark and self.left.empty()) or oldFinal, symbol)

    def empty(self):
        if self._empty is None:  # This needs only be computed once,
            # cache for later use
            self._empty = self.left.empty() and self.right.empty()
        return self._empty

    def updateFinal(self):
        self.left.updateFinal()
        self.right.updateFinal()
        self._final = (self.left.final() and self.right.empty()) or self.right.final()


class Alt(Branch):
    """ Alternation: match left or right """

    def __init__(self, left, right):
        super(Alt, self).__init__(left, right)

    def shift(self, mark, symbol):
        self.left.shift(mark, symbol)
        self.right.shift(mark, symbol)

    def empty(self):
        if self._empty is None:
            self._empty = self.left.empty() or self.right.empty()
        return self._empty

    def updateFinal(self):
        self.left.updateFinal()
        self.right.updateFinal()
        self._final = self.left.final() or self.right.final()

def post2ExprTree(expr):
    pieceStack = []

    while expr:
        sym = expr.pop()

        if sym == ".":  # Concat
            expr2 = pieceStack.pop()
            expr1 = pieceStack.pop()
            pieceStack.append(Seq(expr1, expr2))

        elif sym == "|":
            pieceStack.append(Alt(pieceStack.pop(), pieceStack.pop()))

        elif sym == "*":
            pieceStack.append(Rep(pieceStack.pop()))

        else:
            pieceStack.append(Sym(sym))

    assert len(pieceStack) == 1
    return pieceStack[0]


def match(r, string):
    """ Returns if string matches the regex r """

    if string == "":
        return r.empty()

    r.shift(True, string[0])  # Want to shift in an initial mark to start the
    # NFA

    for c in string[1:]:
        r.updateFinal()  # Explicitly call update here, cache the values
        r.shift(False, c)

    r.updateFinal()
    return r.final()


if __name__ == '__main__':
    r = post2ExprTree(regexToPost("(a.(b.b)*.a)|a.b.c"))
    print(match(r, "abc"))
