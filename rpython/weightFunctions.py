""" RPython doesn't allow for closures, so have to use objects
    instead """

def extractSym(f):
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
    _imutable_fields_ = ["sym"]

    def __init__(self, sym, rig):
        WeightFunctionBase.__init__(self, rig)
        self.sym = sym

    @extractSym
    def call(self, otherSym):
        print(chr(self.sym), chr(otherSym))
        if otherSym == self.sym:
            return self.rig.one
        else:
            return self.rig.zero

def createSingleSymbolMatch(sym, rig):
    return SingleSymbolMatch(sym, rig)

class SymbolClassMatch(WeightFunctionBase):
    #  WARNING: Inverting a characterClass will not always lead
    #  to the expected results for none boolean rigs
    # TODO: Should really implement proper checking for this..., test with int rig

    _imutable_fields_ = ["symMatchClass"]

    def __init__(self, symMatchClass, rig):
        """symMatchClass: a list of weight function objects """
        WeightFunctionBase.__init__(self, rig)
        self.symclass = symMatchClass
        self.rig = rig

    def call(self, sym):
        s = self.rig.zero
        for f in self.symclass:
            s = self.rig.plus(s, f.call(sym))
        return s

class PositionMatcher(WeightFunctionBase):
    _imutable_fields_ = ["sym"]

    def __init__(self, sym, rig):
        WeightFunctionBase.__init__(self, rig)
        self.sym = sym


    def call(self, otherSym):
        print(otherSym, self.sym)
        if otherSym[1] == self.sym:

            return [(0, otherSym[0])]
        else:
            return self.rig.zero

def createPositionMatcher(sym, rig):
    return PositionMatcher(sym, rig)

class CaseInsensitiveWrapper(WeightFunctionBase):
    _imutable_fields_ = ["base"]

    def __init__(self, base, rig):
        WeightFunctionBase.__init__(self, rig)
        self.base = base

    @extractSym
    def call(self, sym):
        return self.base.call((0, ord(chr(sym).lower())))

class InvertWrapper(WeightFunctionBase):
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
    def __init__(self, rig):
        WeightFunctionBase.__init__(self, rig)

    @extractSym
    def call(self, sym):
        if sym == ord("\n"):
            return self.rig.zero
        else:
            return self.rig.one
