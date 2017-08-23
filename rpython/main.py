import os
import sys
from parser import compileRegex, ReSyntaxError, compilePartial
from weightFunctions import createSingleSymbolMatch, createStartPositionMatcher, createStartEndPositionMatcher
from rigs import BitRig, StartPositionRig, StartEndPositionRig
from rpython.rlib.jit import JitDriver

jitdriver = JitDriver(reds=["i", "string", "rig"], greens=["r"])
# QUESTION: Should mode be a green variable?

nModes = 5
PARTIAL_MATCH, COMPLETE_MATCH, FIND_LEFTMOST_START,\
    FIND_LEFTMOST_RANGE, FIND_ALL = range(0, nModes)

def readFile(filename):
    fp = os.open(filename, os.O_RDONLY, 0777)
    f = ""
    while True:
        read = os.read(fp, 4096)
        if len(read) == 0:
            break
        f += read
    os.close(fp)
    return f

def run(re, s, mode):

    print(len(s))
    string = [(i, ord(s[i])) for i in range(len(s))]

    if mode == PARTIAL_MATCH:
        ast = compilePartial(re, BitRig(), createSingleSymbolMatch)
        return mainloop(ast, string, BitRig(), mode)

    elif mode == COMPLETE_MATCH:
        ast = compileRegex(re, BitRig(), createSingleSymbolMatch)
        return mainloop(ast, string, BitRig(), mode)

    elif mode == FIND_LEFTMOST_START:
        ast = compilePartial(re, StartPositionRig(), createStartPositionMatcher)
        return mainloop(ast, string, StartPositionRig(), mode)

    elif mode == FIND_LEFTMOST_RANGE:
        ast = compilePartial(re, StartEndPositionRig(), createStartEndPositionMatcher)
        return mainloop(ast, string, StartEndPositionRig(), mode)
    elif mode == FIND_ALL:
        ast = compilePartial(re, StartEndPositionRig(), createStartEndPositionMatcher)
        return mainloop(ast, string, StartEndPositionRig(), mode)
    else:
        raise ReSyntaxError("Un recognised mode: %d" % mode)

def entry_point(argv):
    try:
        re = argv[1]
        s = readFile(argv[2])
        mode = int(argv[3])
        print(run(re, s, mode))
        """    except IndexError:
        print("Not enough arguments: run in the form re file mode")
        return 1 """
    except ValueError:
        print("Invalid mode option")
        return 1

    return 0

def target(*args):
    return entry_point, None

def jitpolicy(driver):
    from rpython.jit.codewriter.policy import JitPolicy
    return JitPolicy()

def mainloop(r, string, rig, mode):
    """ Returns if string matches the regex r """

    if string == []:
        return r.empty()

    r.shift(rig.one, string[0])  # Want to shift in an initial mark to start the
    # NFA

    i = 0
    ans = [] # TODO: Add variables to red and green list
    potentialNext = rig.zero  # Use this value to avoid adding and then popping from list
    prevAns = rig.zero

    while i < len(string) - 1:  # Main program loop

        jitdriver.can_enter_jit(r=r, i=i, string=string, rig=rig)
        jitdriver.jit_merge_point(r=r, i=i, string=string, rig=rig)

        r.updateFinal()  # Explicitly call update here, cache the values
        print((i+1, "%s" % chr(string[i+1][1]), r.final()))
        if mode ==  FIND_ALL:
            r.updateFinal()
            if r.final() == prevAns and prevAns != rig.zero and prevAns != rig.one:
                # The longest leftmost match has been found. Reset FSM and start
                # from the character at the end of the match
                print(i+1)
                ans.append(r.final())
                r.reset()
                r.shift(rig.one, string[i])
                prevAns = rig.zero
            else:
                prevAns = r.final()
                r.shift(rig.zero, string[i+1])
                i += 1

        else:
            r.updateFinal()
            r.shift(rig.zero, string[i+1])
            i += 1

    #    r.shift(rig.one, string[i+1])  # Modify for modes...

    # TODO:  Find a way to use fewer conditions
    r.updateFinal()
    if r.final() != rig.zero and r.final() != rig.one:
        ans.append(r.final())

    if potentialNext != rig.zero:
        ans.append(potentialNext)
    print(ans)
    return r.final()

if __name__ == '__main__':
    entry_point(sys.argv)
