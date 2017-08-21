import os
import sys
from parser import compileRegex, ReSyntaxError, compilePartial
from weightFunctions import createSingleSymbolMatch, createPositionMatcher
from rigs import BitRig, PositionRig
from rpython.rlib.jit import JitDriver

jitdriver = JitDriver(reds=["i", "string", "rig"], greens=["r"])
# QUESTION: Should mode be a green variable?

PARTIAL_MATCH, COMPLETE_MATCH, FIND_LEFTMOST = range(0,3)

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
        return mainloop(ast, string, BitRig())

    elif mode == COMPLETE_MATCH:
        ast = compileRegex(re, BitRig(), createSingleSymbolMatch)
        return mainloop(ast, string, BitRig())

    elif mode == FIND_LEFTMOST:
        ast = compileRegex(re, PositionRig(), createPositionMatcher)
        """    zippedList = []
        for i in range(len(string)):
            zippedList.append((i, string[i]))  # For some reason list(enumerate(string)) causes RPython to hang?
        """
        return mainloop(ast, string, PositionRig())

    else:
        raise ReSyntaxError("Un recognised mode: %d" % mode)


def entry_point(argv):
    try:
        re = argv[1]
        s = readFile(argv[2])
        mode = int(argv[3])
        print(run(re, s, mode))
    except IndexError:
        print("Not enough arguments: run in the form re file mode")
        return 1
    except ValueError:
        print("Invalid mode option")
        return 1

    return 0

def target(*args):
    return entry_point, None

def jitpolicy(driver):
    from rpython.jit.codewriter.policy import JitPolicy
    return JitPolicy()



def mainloop(r, string, rig):
    """ Returns if string matches the regex r """

    if string == []:
        return r.empty()

    r.shift(r._rig.one, string[0])  # Want to shift in an initial mark to start the
    # NFA

    i = 0
    while i < len(string) - 1:  # Main program loop
        jitdriver.can_enter_jit(r=r, i=i, string=string, rig=rig)
        jitdriver.jit_merge_point(r=r, i=i, string=string, rig=rig)

        r.updateFinal()  # Explicitly call update here, cache the values
        r.shift(rig.zero, string[i+1])
        i += 1

    r.updateFinal()
    return r.final()

if __name__ == '__main__':
    entry_point(sys.argv)
