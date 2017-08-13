from Queue import Queue

class State:
    """ A state class for an NFA_eps """

    def __init__(self, symbol, epsTransitions, match):
        self.symbol = symbol  # TODO: Think of a better way to write the symbol
        self.symbolTransition = None  # Will get linked into later
        self.epsTransitions = epsTransitions
        self.match = match

    def transition(self, symbol):
        if self.symbol and symbol == self.symbol:
            return {self.symbolTransition}
        return {}

    def __repr__(self):
        if self.match:
            return "Match"
        elif self.symbol is not None:
            return self.symbol
        else:
            return "_"

class Fragment:
    """ A fragment of the NFA, consisting of one or more states """

    def __init__(self, inState, outStates):
        self.inState = inState
        self.outStates = outStates

    def link(self, nextState):
        """ Links the dangling states in the fragment to the next state """
        assert nextState != None
        for state in self.outStates:
            if not state.symbol:
                state.epsTransitions.add(nextState)
            else:
                state.symbolTransition = nextState

def buildNfa(regExp):
    """ Initial attempt based off of https://swtch.com/~rsc/regexp/regexp1.html by Russ Cox"""

    fragmentStack = []

    while regExpStack:
        sym = regExpStack.pop()

        if sym == ".":  # Concat
            expr2 = fragmentStack.pop()
            expr1 = fragmentStack.pop()
            expr1.link(expr2.inState)
            fragmentStack.append(Fragment(expr1.inState, expr2.outStates))

        elif sym == "|":  # Alternation
            expr2 = fragmentStack.pop()
            expr1 = fragmentStack.pop()
            split = State(None, {expr1.inState, expr2.inState}, False)
            fragmentStack.append(Fragment(split, expr1.outStates | expr2.outStates))

        elif sym == "?":  # Zero or one
            expr = fragmentStack.pop()
            split = State(None, {expr.inState}, False)
            fragmentStack.append(Fragment(split, {split} | expr.outStates))

        elif sym == "*":  # Zero or more
            expr = fragmentStack.pop()
            loop = State(None, {expr.inState}, False)
            expr.link(loop)
            fragmentStack.append(Fragment(loop, {loop}))

        elif sym == "+":  # One or more
            expr = fragmentStack.pop()
            loop = State(None, {expr.inState}, False)
            expr.link(loop)
            fragmentStack.append(Fragment(expr.inState, {loop}))

        else:
            state = State(sym, {}, False)
            fragmentStack.append(Fragment(state, {state}))

    final = fragmentStack.pop()
    assert fragmentStack == []
    final.link(State(None, {}, True))
    return final.inState


def match(startState, symbolList):
    """ Takes the start state to an NFA, a string and checks to see if
        the NFA matches """

    def addState(state, stateSet):  # TODO: Optimise this function
        if state not in stateSet:
            stateSet.add(state)
            for nextState in state.epsTransitions:
                addState(nextState, stateSet)

    states = set()
    addState(startState, states)

    for sym in symbolList:
        nextStates = set()

        for state in states:
            for nextState in state.transition(sym):
                addState(nextState, nextStates)

        states = nextStates

    for state in states:
        if state.match:
            return True
    return False

def check(regEx, s):
    return match(buildNfa(regexToPost(regEx)), s)

if __name__ == '__main__':
    print(check("a|b*", "bbbabbb"))
