""" These are wrapper classes for weight functions: as
    RPython doesn't allow for closures, so have to use objects
    instead """

def extractSym(f):
    # Extracts the actual character, ignoring position information
    def wrapper(self, sym):
        return f(self, sym[1])

    return wrapper

class WeightFunctionBase(object):
    """ Abstract base class """

    _imutable_fields_ = ["rig"]

    def __init__(self, rig):
        self.rig = rig

    def call(self, sym):  # Just to allow for static typing
        return self.rig.zero

class SingleSymbolMatch(WeightFunctionBase):
    """ Returns a one if the symbols match, a zero otherwise """
    _imutable_fields_ = ["sym"]

    def __init__(self, sym, rig):
        WeightFunctionBase.__init__(self, rig)
        self.sym = sym

    @extractSym
    def call(self, otherSym):
        if otherSym == self.sym:
            return self.rig.one
        else:
            return self.rig.zero

def createSingleSymbolMatch(sym, rig):
    return SingleSymbolMatch(sym, rig)

class SymbolClassMatch(WeightFunctionBase):
    """ Creates a matcher for a character class: takes a list of single symbol
        matchers and adds together the call for each one"""

    _imutable_fields_ = ["symMatchClass"]

    def __init__(self, symMatchClass, rig):
        # symMatchClass is a list of weight function objects
        WeightFunctionBase.__init__(self, rig)
        self.symclass = symMatchClass
        self.rig = rig

    def call(self, sym):
        s = self.rig.zero
        for f in self.symclass:
            s = self.rig.plus(s, f.call(sym))
        return s

class StartPositionMatcher(WeightFunctionBase):
    """ A matcher that returns the position of the char if
        it matches in the form (0, n), a zero otherwise """

    _imutable_fields_ = ["sym"]

    def __init__(self, sym, rig):
        WeightFunctionBase.__init__(self, rig)
        self.sym = sym

    def call(self, otherSym):
        if otherSym[1] == self.sym:
            return (0, otherSym[0])
        else:
            return self.rig.zero

def createStartPositionMatcher(sym, rig):
    return StartPositionMatcher(sym, rig)

class StartEndPositionMatcher(WeightFunctionBase):
        """ A matcher for finding the start and end of a submatch. """

        _imutable_fields_ = ["sym"]

        def __init__(self, sym, rig):
            WeightFunctionBase.__init__(self, rig)
            self.sym = sym

        def call(self, otherSym):
            if otherSym[1] == self.sym:
                return (otherSym[0], otherSym[0])
            else:
                return self.rig.zero

def createStartEndPositionMatcher(sym, rig):
    return StartEndPositionMatcher(sym, rig)

class CaseInsensitiveWrapper(WeightFunctionBase):
    """ Takes a weight function and makes it case insensitive """
    _imutable_fields_ = ["base"]

    def __init__(self, base, rig):
        WeightFunctionBase.__init__(self, rig)
        self.base = base

    @extractSym
    def call(self, sym):
        return self.base.call((0, ord(chr(sym).lower())))

class InvertWrapper(WeightFunctionBase):
    """ Takes a weight function and inverts it; that is, if a zero is returned
        originally, return a one; otherwise return a zero """
    _imutable_fields_ = ["base"]

    def __init__(self, base, rig):
        WeightFunctionBase.__init__(self, rig)
        self.base = base

    def call(self, sym):
        if self.base.call(sym) == self.rig.zero:
            return self.rig.one
        else:
            return self.rig.zero

class AllButNewLineMatcher(WeightFunctionBase):
    """ Returns a "match" (as defined by the rig) unless the symbol is a newline"""

    def __init__(self, rig):
        WeightFunctionBase.__init__(self, rig)

    def call(self, sym):
        if sym[1] == 10:  # ord(\n) == 10
            return self.rig.zero
        else:
            return self.rig.autoMatch(sym)

class OneProducer(WeightFunctionBase):
    """ Always returns a one """
    def __init__(self, rig):
        WeightFunctionBase.__init__(self, rig)

    def call(self, sym):
        return self.rig.one

class ZeroProducer(WeightFunctionBase):
    """ Always returns a zero """
    def __init__(self, rig):
        WeightFunctionBase.__init__(self, rig)

    def call(self, sym):
        return self.rig.zero
